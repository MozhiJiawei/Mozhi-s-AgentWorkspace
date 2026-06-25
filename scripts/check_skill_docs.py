from __future__ import annotations

import argparse
import configparser
import hashlib
from pathlib import Path
import re
import sys


MANIFEST_PATH = Path("docs/skill-docs.yml")
DOCS_MANIFEST_NAME = "docs.manifest.yml"
DOC_FINGERPRINT_PATTERNS = (
    DOCS_MANIFEST_NAME,
    "README.md",
    "SKILL.md",
    "REQUIREMENTS.md",
    "AGENTS.md",
    "docs/**/*",
    "references/**/*.md",
)


def parse_docs_manifest(path: Path) -> dict[str, object]:
    data: dict[str, object] = {"nav": []}
    current_nav_item: dict[str, str] | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        scalar_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.+?)\s*$", line)
        if scalar_match:
            data[scalar_match.group(1)] = strip_yaml_scalar(scalar_match.group(2))
            current_nav_item = None
            continue

        nav_item_match = re.match(r"^  - title:\s*(.+?)\s*$", line)
        if nav_item_match:
            current_nav_item = {"title": strip_yaml_scalar(nav_item_match.group(1))}
            nav = data.setdefault("nav", [])
            assert isinstance(nav, list)
            nav.append(current_nav_item)
            continue

        nav_path_match = re.match(r"^    path:\s*(.+?)\s*$", line)
        if nav_path_match and current_nav_item is not None:
            current_nav_item["path"] = strip_yaml_scalar(nav_path_match.group(1))

    return data


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


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_manifest(text: str) -> dict[str, dict[str, str]]:
    skills_match = re.search(r"^skills:\s*$", text, flags=re.MULTILINE)
    if not skills_match:
        return {}

    skills: dict[str, dict[str, str]] = {}
    current_name: str | None = None
    in_publish = False
    in_review = False

    for line in text[skills_match.end() :].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        skill_match = re.match(r"^  ([^\s:\n][^:\n]*):\s*$", line)
        if skill_match:
            current_name = skill_match.group(1).strip()
            skills[current_name] = {}
            in_publish = False
            in_review = False
            continue

        if current_name is None:
            continue

        path_match = re.match(r"^    path:\s*(.+?)\s*$", line)
        if path_match:
            skills[current_name]["path"] = strip_yaml_scalar(path_match.group(1))
            continue

        mount_match = re.match(r"^    mount:\s*(.+?)\s*$", line)
        if mount_match:
            skills[current_name]["mount"] = strip_yaml_scalar(mount_match.group(1))
            continue

        status_match = re.match(r"^    status:\s*(.+?)\s*$", line)
        if status_match:
            skills[current_name]["status"] = strip_yaml_scalar(status_match.group(1))
            continue

        publish_match = re.match(r"^    publish:\s*$", line)
        if publish_match:
            in_publish = True
            in_review = False
            continue

        review_match = re.match(r"^    docs_review:\s*$", line)
        if review_match:
            in_publish = False
            in_review = True
            continue

        section_match = re.match(r"^    [A-Za-z0-9_-]+:\s*", line)
        if section_match:
            in_publish = False
            in_review = False

        if in_publish:
            mode_match = re.match(r"^      mode:\s*(.+?)\s*$", line)
            if mode_match:
                skills[current_name]["mode"] = strip_yaml_scalar(mode_match.group(1))
                continue

            entry_match = re.match(r"^      entry:\s*(.+?)\s*$", line)
            if entry_match:
                skills[current_name]["entry"] = strip_yaml_scalar(entry_match.group(1))
                continue

            skill_manifest_match = re.match(r"^      skill_manifest:\s*(.+?)\s*$", line)
            if skill_manifest_match:
                skills[current_name]["skill_manifest"] = strip_yaml_scalar(
                    skill_manifest_match.group(1)
                )
                continue

        if in_review:
            fingerprint_match = re.match(r"^      source_fingerprint:\s*(.+?)\s*$", line)
            if fingerprint_match:
                skills[current_name]["source_fingerprint"] = strip_yaml_scalar(
                    fingerprint_match.group(1)
                )

    return skills


def docs_files(skill_root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in DOC_FINGERPRINT_PATTERNS:
        files.update(path for path in skill_root.glob(pattern) if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(skill_root).as_posix())


def source_fingerprint(skill_root: Path) -> str:
    digest = hashlib.sha256()
    for path in docs_files(skill_root):
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
        raise ValueError(f"找不到 skill 的文档登记块：{skill_name}")

    block = match.group(1)
    updated_block, count = re.subn(
        r"(^      source_fingerprint:\s*).*$",
        rf"\g<1>{fingerprint}",
        block,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise ValueError(f"找不到 skill 的 source_fingerprint：{skill_name}")
    return text[: match.start(1)] + updated_block + text[match.end(1) :]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查 skill 文档集成登记是否存在且保持最新。"
    )
    parser.add_argument(
        "--update-fingerprints",
        action="store_true",
        help="复核文档变化后刷新 docs_review.source_fingerprint。",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    manifest_path = root / MANIFEST_PATH
    if not manifest_path.exists():
        print(f"缺少 {MANIFEST_PATH.as_posix()}")
        return 1

    text = manifest_path.read_text(encoding="utf-8")
    manifest = parse_manifest(text)
    if not manifest:
        print(f"{MANIFEST_PATH.as_posix()} 缺少可读取的 skills 区段。")
        return 1

    registered_paths = parse_gitmodule_skill_paths(root)
    manifest_by_path = {
        data.get("path", "").replace("\\", "/"): name for name, data in manifest.items()
    }

    errors: list[str] = []
    missing_paths = [path for path in registered_paths if path not in manifest_by_path]
    if missing_paths:
        errors.append("以下 skill submodule 缺少文档集成登记：")
        errors.extend(f"  - {path}" for path in missing_paths)

    updated_text = text
    checked = 0
    changed = 0

    for name, data in manifest.items():
        relative_path = data.get("path", "").replace("\\", "/")
        if not relative_path:
            errors.append(f"{name}: 缺少 path")
            continue

        skill_root = root / relative_path
        if not skill_root.exists():
            errors.append(f"{name}: path 不存在：{relative_path}")
            continue

        entry = data.get("entry", "")
        if not entry:
            errors.append(f"{name}: 缺少 publish.entry")

        mode = data.get("mode", "")
        if mode not in {"placeholder", "subrepo-manifest"}:
            errors.append(f"{name}: publish.mode 必须是 placeholder 或 subrepo-manifest")
        if mode == "placeholder" and entry and not (root / entry).is_file():
            errors.append(f"{name}: publish.entry 不存在：{entry}")

        skill_manifest = data.get("skill_manifest", DOCS_MANIFEST_NAME)
        skill_manifest_path = skill_root / skill_manifest
        has_skill_manifest = skill_manifest_path.is_file()
        if mode == "subrepo-manifest" and not has_skill_manifest:
            errors.append(f"{name}: 缺少必需的 skill 文档 manifest：{skill_manifest}")
        if mode == "subrepo-manifest" and has_skill_manifest:
            docs_manifest = parse_docs_manifest(skill_manifest_path)
            for required_field in ("schema_version", "name", "title", "description", "entry"):
                if not docs_manifest.get(required_field):
                    errors.append(f"{name}: {skill_manifest} 缺少 {required_field}")

            declared_paths: list[str] = []
            entry_path = str(docs_manifest.get("entry", "")).replace("\\", "/")
            if entry_path:
                declared_paths.append(entry_path)

            nav = docs_manifest.get("nav", [])
            if not isinstance(nav, list) or not nav:
                errors.append(f"{name}: {skill_manifest} 缺少 nav")
            elif isinstance(nav, list):
                for item in nav:
                    if not isinstance(item, dict):
                        errors.append(f"{name}: {skill_manifest} 包含无法读取的 nav 项")
                        continue
                    if not item.get("title") or not item.get("path"):
                        errors.append(f"{name}: {skill_manifest} 的 nav 项缺少 title 或 path")
                        continue
                    declared_paths.append(str(item["path"]).replace("\\", "/"))

            for declared_path in sorted(set(declared_paths)):
                if not (skill_root / declared_path).is_file():
                    errors.append(f"{name}: manifest 声明的文档文件不存在：{declared_path}")
        if mode == "placeholder" and has_skill_manifest:
            errors.append(
                f"{name}: {skill_manifest} 已存在；请将 publish.mode 切换为 "
                "subrepo-manifest，并刷新文档指纹。"
            )

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
                f"{name}: 与文档相关的文件已变化；请复核发布文档，并使用 "
                "`python scripts/check_skill_docs.py --update-fingerprints` "
                "刷新 docs_review.source_fingerprint。"
            )

    if args.update_fingerprints:
        if changed:
            manifest_path.write_text(updated_text, encoding="utf-8")
            print(f"已更新 {changed} 个 skill 的文档指纹。")
        else:
            print("文档指纹已是最新。")
        return 0 if not errors else 1

    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"Skill 文档检查通过，共检查 {checked} 个 skill。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
