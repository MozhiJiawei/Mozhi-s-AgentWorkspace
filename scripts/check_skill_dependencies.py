from __future__ import annotations

import argparse
import configparser
import hashlib
from pathlib import Path
import re
import sys


MANIFEST_PATH = Path("docs/skill-dependencies.yml")
SELF_CHECK_SCRIPT = "verify_dependencies.py"
FINGERPRINT_PATTERNS = (
    "SKILL.md",
    SELF_CHECK_SCRIPT,
    "requirements*.txt",
    "pyproject.toml",
    "environment*.yml",
    "environment*.yaml",
    "package.json",
    "scripts/**/*.py",
    "install*.ps1",
    "install*.sh",
    "install*.bat",
)


def parse_gitmodule_skill_paths(root: Path) -> list[str]:
    gitmodules_path = root / ".gitmodules"
    if not gitmodules_path.exists():
        return []

    parser = configparser.ConfigParser()
    parser.read(gitmodules_path, encoding="utf-8")
    paths: list[str] = []
    for section in parser.sections():
        if parser.has_option(section, "path"):
            path = parser.get(section, "path").strip().replace("\\", "/")
            if path.startswith("skills/"):
                paths.append(path)
    return sorted(paths)


def parse_manifest(text: str) -> dict[str, dict[str, str]]:
    skills_match = re.search(r"^skills:\s*$", text, flags=re.MULTILINE)
    if not skills_match:
        return {}

    skills: dict[str, dict[str, str]] = {}
    current_name: str | None = None
    in_review = False

    for line in text[skills_match.end() :].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        skill_match = re.match(r"^  ([^\s:\n][^:\n]*):\s*$", line)
        if skill_match:
            current_name = skill_match.group(1).strip()
            skills[current_name] = {}
            in_review = False
            continue

        if current_name is None:
            continue

        path_match = re.match(r"^    path:\s*(.+?)\s*$", line)
        if path_match:
            skills[current_name]["path"] = strip_yaml_scalar(path_match.group(1))
            continue

        review_match = re.match(r"^    dependency_review:\s*$", line)
        if review_match:
            in_review = True
            continue

        section_match = re.match(r"^    [A-Za-z0-9_-]+:\s*", line)
        if section_match:
            in_review = False

        if in_review:
            fingerprint_match = re.match(r"^      source_fingerprint:\s*(.+?)\s*$", line)
            if fingerprint_match:
                skills[current_name]["source_fingerprint"] = strip_yaml_scalar(
                    fingerprint_match.group(1)
                )

    return skills


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def dependency_files(skill_root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in FINGERPRINT_PATTERNS:
        files.update(path for path in skill_root.glob(pattern) if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(skill_root).as_posix())


def source_fingerprint(skill_root: Path) -> str:
    digest = hashlib.sha256()
    for path in dependency_files(skill_root):
        relative = path.relative_to(skill_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def replace_fingerprint(text: str, skill_name: str, fingerprint: str) -> str:
    skill_pattern = re.compile(
        rf"(^  {re.escape(skill_name)}:\n(?:^    .*\n|^      .*\n|^        .*\n|^        - .*\n|^\s*$)*)",
        flags=re.MULTILINE,
    )
    match = skill_pattern.search(text)
    if not match:
        raise ValueError(f"Cannot find manifest block for skill: {skill_name}")

    block = match.group(1)
    updated_block, count = re.subn(
        r"(^      source_fingerprint:\s*).*$",
        rf"\g<1>{fingerprint}",
        block,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise ValueError(f"Cannot find source_fingerprint for skill: {skill_name}")
    return text[: match.start(1)] + updated_block + text[match.end(1) :]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that skill dependency reviews are present and up to date."
    )
    parser.add_argument(
        "--update-fingerprints",
        action="store_true",
        help="Refresh dependency_review.source_fingerprint after manually reviewing dependencies.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    manifest_path = root / MANIFEST_PATH
    if not manifest_path.exists():
        print(f"Missing {MANIFEST_PATH.as_posix()}")
        return 1

    text = manifest_path.read_text(encoding="utf-8")
    manifest = parse_manifest(text)
    if not manifest:
        print(f"{MANIFEST_PATH.as_posix()} does not contain a readable skills section.")
        return 1

    registered_paths = parse_gitmodule_skill_paths(root)
    manifest_by_path = {
        data.get("path", "").replace("\\", "/"): name for name, data in manifest.items()
    }

    errors: list[str] = []
    missing_paths = [path for path in registered_paths if path not in manifest_by_path]
    if missing_paths:
        errors.append("Skill submodules missing from dependency manifest:")
        errors.extend(f"  - {path}" for path in missing_paths)

    updated_text = text
    checked = 0
    changed = 0

    for name, data in manifest.items():
        relative_path = data.get("path", "").replace("\\", "/")
        if not relative_path:
            errors.append(f"{name}: missing path")
            continue

        skill_root = root / relative_path
        if not skill_root.exists():
            errors.append(f"{name}: path does not exist: {relative_path}")
            continue
        if not (skill_root / SELF_CHECK_SCRIPT).is_file():
            errors.append(
                f"{name}: missing required self-check script: "
                f"{relative_path}/{SELF_CHECK_SCRIPT}"
            )
            continue

        expected = data.get("source_fingerprint")
        actual = source_fingerprint(skill_root)
        checked += 1

        if args.update_fingerprints:
            if expected != actual:
                updated_text = replace_fingerprint(updated_text, name, actual)
                changed += 1
            continue

        if expected != actual:
            errors.append(
                f"{name}: dependency-relevant files changed; review dependencies and refresh "
                f"dependency_review.source_fingerprint with "
                f"`python scripts/check_skill_dependencies.py --update-fingerprints`."
            )

    if args.update_fingerprints:
        if changed:
            manifest_path.write_text(updated_text, encoding="utf-8")
            print(f"Updated dependency fingerprints for {changed} skill(s).")
        else:
            print("Dependency fingerprints already up to date.")
        return 0 if not errors else 1

    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"Skill dependency check passed for {checked} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
