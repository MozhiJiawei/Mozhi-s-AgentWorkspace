from __future__ import annotations

import configparser
import json
import shutil
from pathlib import Path
import re


SKILL_DOCS_ROOT = Path("docs/skills")
SUBREPO_MANIFEST = "docs.manifest.yml"
GENERATED_ROOT = Path("docs/.vitepress/generated")
BETA_SKILL_NAMES = {"generate-3plus1-diagrams"}
SKILL_ORDER = {
    "ppt-deep-search": 0,
    "huawei-pptx-generator": 1,
}


def display_skill_title(skill: dict[str, object]) -> str:
    title = str(skill["title"])
    if title in BETA_SKILL_NAMES:
        return f"[beta] {title}"
    return title


def skill_sort_key(skill: dict[str, object]) -> tuple[int, str]:
    title = str(skill["title"])
    if title in BETA_SKILL_NAMES:
        return (99, title)
    return (SKILL_ORDER.get(title, 50), title)


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


def copy_declared_docs(root: Path, skill_path: str) -> dict[str, object]:
    skill_root = root / skill_path
    manifest_path = skill_root / SUBREPO_MANIFEST
    manifest = parse_docs_manifest(manifest_path)

    skill_slug = Path(skill_path).name
    target_root = root / SKILL_DOCS_ROOT / skill_slug
    if target_root.exists():
        shutil.rmtree(target_root)
    target_root.mkdir(parents=True, exist_ok=True)

    declared_paths: list[str] = []
    entry = str(manifest.get("entry", "")).replace("\\", "/")
    if entry:
        declared_paths.append(entry)

    nav = manifest.get("nav", [])
    if isinstance(nav, list):
        for item in nav:
            if isinstance(item, dict) and item.get("path"):
                declared_paths.append(str(item["path"]).replace("\\", "/"))

    path_to_destination: dict[str, str] = {}
    copied: set[str] = set()
    for relative in declared_paths:
        if relative in copied:
            continue
        copied.add(relative)
        source = skill_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"{skill_path}: missing declared docs file: {relative}")

        destination_name = Path(relative).name
        if relative == entry:
            destination_name = "index.md"
        destination = target_root / destination_name
        path_to_destination[relative] = destination_name
        destination.write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    if entry:
        index_path = target_root / "index.md"
        index_text = index_path.read_text(encoding="utf-8")
        nav_lines = ["", "## 子仓文档导航", ""]
        if isinstance(nav, list):
            for item in nav:
                if not isinstance(item, dict):
                    continue
                title = item.get("title")
                source_path = str(item.get("path", "")).replace("\\", "/")
                destination_name = path_to_destination.get(source_path)
                if title and destination_name:
                    link = "./" if destination_name == "index.md" else f"./{destination_name}"
                    nav_lines.append(f"- [{title}]({link})")
        index_path.write_text(index_text.rstrip() + "\n" + "\n".join(nav_lines) + "\n", encoding="utf-8")

    sidebar_items: list[dict[str, str]] = []
    if isinstance(nav, list):
        for item in nav:
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            source_path = str(item.get("path", "")).replace("\\", "/")
            destination_name = path_to_destination.get(source_path)
            if title and destination_name:
                link = f"/skills/{skill_slug}/"
                if destination_name != "index.md":
                    link = f"/skills/{skill_slug}/{Path(destination_name).stem}"
                sidebar_items.append({"text": str(title), "link": link})

    return {
        "slug": skill_slug,
        "title": str(manifest.get("name", skill_slug)),
        "description": str(manifest.get("description", "")),
        "items": sidebar_items,
    }


def write_skill_index(root: Path, skills: list[dict[str, object]]) -> None:
    lines = [
        "# Skills",
        "",
        "以下内容由各 skill 子仓的 `docs.manifest.yml` 集成生成。",
        "",
    ]

    for skill in sorted(skills, key=skill_sort_key):
        lines.append(f"## [{display_skill_title(skill)}](./{skill['slug']}/)")
        if skill["description"]:
            lines.append("")
            lines.append(skill["description"])
        lines.append("")

    (root / SKILL_DOCS_ROOT / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_skill_sidebar(root: Path, skills: list[dict[str, object]]) -> None:
    GENERATED_ROOT_PATH = root / GENERATED_ROOT
    GENERATED_ROOT_PATH.mkdir(parents=True, exist_ok=True)

    sidebar_items: list[dict[str, object]] = [{"text": "Skills", "link": "/skills/"}]
    for skill in sorted(skills, key=skill_sort_key):
        items = skill.get("items", [])
        if not isinstance(items, list):
            items = []
        sidebar_items.append(
            {
                "text": display_skill_title(skill),
                "collapsed": True,
                "items": items,
            }
        )

    (GENERATED_ROOT_PATH / "skill-sidebar.json").write_text(
        json.dumps(sidebar_items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    skill_docs_manifest = root / "docs" / "skill-docs.yml"
    if not skill_docs_manifest.exists():
        print("Missing docs/skill-docs.yml")
        return 1

    synced: list[dict[str, object]] = []
    for skill_path in parse_gitmodule_skill_paths(root):
        manifest_path = root / skill_path / SUBREPO_MANIFEST
        if not manifest_path.is_file():
            raise FileNotFoundError(f"{skill_path}: missing {SUBREPO_MANIFEST}")
        synced.append(copy_declared_docs(root, skill_path))

    write_skill_index(root, synced)
    write_skill_sidebar(root, synced)
    print(f"synced {len(synced)} skill documentation set(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
