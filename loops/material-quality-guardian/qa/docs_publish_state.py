from __future__ import annotations

import configparser
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Iterable

from common import repo_root

ROOT = repo_root()
SKILL_DOCS_MANIFEST = ROOT / "docs" / "skill-docs.yml"
WORKSPACE_DOCS_ROOT = ROOT / "docs"
WORKSPACE_EXCLUDED_PREFIXES = (
    ".vitepress/cache/",
    ".vitepress/dist/",
    ".vitepress/generated/",
    "public/material-quality/",
    "public/skill-static/",
    "skills/",
)
SKILL_DOC_PATTERNS = (
    "docs.manifest.yml",
    "docs/**/*",
    "references/**/*.md",
)


def _run_git(args: list[str], cwd: Path = ROOT) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def parse_skill_docs_manifest(path: Path = SKILL_DOCS_MANIFEST) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    skills: dict[str, dict[str, str]] = {}
    current_name: str | None = None
    section: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line == "skills:":
            continue

        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            current_name = line.strip().removesuffix(":")
            skills[current_name] = {}
            section = None
            continue

        if current_name is None:
            continue

        if line.startswith("    ") and line.strip().endswith(":"):
            section = line.strip().removesuffix(":")
            continue

        if line.startswith("    ") and ":" in line and section is None:
            key, value = line.strip().split(":", 1)
            skills[current_name][key] = _strip_yaml_scalar(value)
            continue

        if line.startswith("      ") and ":" in line and section is not None:
            key, value = line.strip().split(":", 1)
            skills[current_name][f"{section}.{key}"] = _strip_yaml_scalar(value)

    return skills


def parse_gitmodule_skill_paths(root: Path = ROOT) -> list[str]:
    gitmodules_path = root / ".gitmodules"
    if not gitmodules_path.exists():
        return []

    parser = configparser.ConfigParser()
    parser.read(gitmodules_path, encoding="utf-8")
    paths: list[str] = []
    for section in parser.sections():
        if parser.has_option(section, "path"):
            rel = parser.get(section, "path").strip().replace("\\", "/")
            if rel.startswith("skills/"):
                paths.append(rel)
    return sorted(paths)


def _strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _iter_workspace_source_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for path in sorted((root / "docs").rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root / "docs").as_posix()
        if rel.startswith(WORKSPACE_EXCLUDED_PREFIXES):
            continue
        files.append(path)
    return files


def _iter_skill_source_files(skill_root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in SKILL_DOC_PATTERNS:
        files.update(path for path in skill_root.glob(pattern) if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(skill_root).as_posix())


def _fingerprint_files(base: Path, files: Iterable[Path]) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for path in files:
        count += 1
        relative = path.relative_to(base).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}", count


def collect_publish_state(root: Path = ROOT) -> dict[str, object]:
    workspace_files = _iter_workspace_source_files(root)
    workspace_fingerprint, workspace_count = _fingerprint_files(root / "docs", workspace_files)

    manifest = parse_skill_docs_manifest(root / "docs" / "skill-docs.yml")
    registered_paths = set(parse_gitmodule_skill_paths(root))

    skills: list[dict[str, object]] = []
    for skill_name, data in sorted(manifest.items()):
        relative_path = data.get("path", "").replace("\\", "/")
        if not relative_path or relative_path not in registered_paths:
            continue

        skill_root = root / relative_path
        files = _iter_skill_source_files(skill_root)
        fingerprint, file_count = _fingerprint_files(skill_root, files)
        skills.append(
            {
                "name": skill_name,
                "path": relative_path,
                "mount": data.get("mount", ""),
                "publish_mode": data.get("publish.mode", ""),
                "entry": data.get("publish.entry", ""),
                "source_commit": _run_git(["rev-parse", "HEAD"], skill_root),
                "source_fingerprint": fingerprint,
                "source_file_count": file_count,
            }
        )

    overall = hashlib.sha256()
    overall.update(workspace_fingerprint.encode("utf-8"))
    for skill in skills:
        overall.update(str(skill["name"]).encode("utf-8"))
        overall.update(b"\0")
        overall.update(str(skill["source_fingerprint"]).encode("utf-8"))
        overall.update(b"\0")

    return {
        "schema_version": 1,
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "repository": "Mozhi-s-AgentWorkspace",
        "main_commit": _run_git(["rev-parse", "HEAD"], root),
        "workspace_docs": {
            "source_fingerprint": workspace_fingerprint,
            "source_file_count": workspace_count,
        },
        "skills": skills,
        "overall_source_fingerprint": f"sha256:{overall.hexdigest()}",
    }


def write_publish_state(output_path: Path, root: Path = ROOT) -> dict[str, object]:
    state = collect_publish_state(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state
