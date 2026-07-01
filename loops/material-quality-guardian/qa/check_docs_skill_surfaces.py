from __future__ import annotations

import json
from pathlib import Path
import re

from common import repo_root


MANIFEST_PATH = Path("docs/skill-docs.yml")
SKILLS_ROOT = Path("skills")
HOME_INDEX_PATH = Path("docs/index.md")
SKILL_INDEX_PATH = Path("docs/skills/index.md")
SIDEBAR_PATH = Path("docs/.vitepress/generated/skill-sidebar.json")
DOCS_MANIFEST_NAME = "docs.manifest.yml"
REQUIRED_SKILL_NAV_TITLES = ("能力展示", "使用方式", "依赖说明", "架构概览")


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_skill_docs_manifest(text: str) -> dict[str, dict[str, str]]:
    skills_match = re.search(r"^skills:\s*$", text, flags=re.MULTILINE)
    if not skills_match:
        return {}

    skills: dict[str, dict[str, str]] = {}
    current_name: str | None = None
    for line in text[skills_match.end() :].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        skill_match = re.match(r"^  ([^\s:\n][^:\n]*):\s*$", line)
        if skill_match:
            current_name = skill_match.group(1).strip()
            skills[current_name] = {}
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

    return skills


def parse_subrepo_docs_manifest(text: str) -> dict[str, object]:
    data: dict[str, object] = {"nav": []}
    current_nav_item: dict[str, str] | None = None

    for line in text.splitlines():
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


def repo_skill_paths(root: Path) -> set[str]:
    skills_root = root / SKILLS_ROOT
    if not skills_root.is_dir():
        return set()

    paths: set[str] = set()
    for child in skills_root.iterdir():
        if not child.is_dir():
            continue
        if (child / "SKILL.md").is_file() or (child / DOCS_MANIFEST_NAME).is_file():
            paths.add(child.relative_to(root).as_posix())
    return paths


def expected_skill_links(skills: dict[str, dict[str, str]]) -> dict[str, str]:
    links: dict[str, str] = {}
    for name, data in skills.items():
        mount = data.get("mount", "").replace("\\", "/")
        if not mount.startswith("docs/skills/"):
            continue
        links[name] = "/" + mount.removeprefix("docs").strip("/") + "/"
    return links


def normalize_site_link(link: str) -> str:
    link = link.strip()
    if link.startswith("./"):
        link = "/skills/" + link.removeprefix("./")
    if not link.startswith("/"):
        return link.rstrip("/")
    return "/" + link.strip("/") + "/"


def markdown_links(text: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"\[[^\n]*?\]\(([^)\n]+)\)", text)]


def home_skill_section(text: str) -> str:
    match = re.search(r"^## 当前支持的 Skills\s*$", text, flags=re.MULTILINE)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    if not next_heading:
        return text[match.end() :]
    return text[match.end() : match.end() + next_heading.start()]


def sidebar_skill_links(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    links: set[str] = set()
    if not isinstance(data, list):
        return links
    for item in data:
        if not isinstance(item, dict):
            continue
        direct_link = item.get("link")
        if isinstance(direct_link, str) and direct_link.startswith("/skills/"):
            links.add(normalize_site_link(direct_link))
        child_items = item.get("items", [])
        if not isinstance(child_items, list):
            continue
        for child in child_items:
            if not isinstance(child, dict):
                continue
            link = child.get("link")
            if isinstance(link, str) and link.startswith("/skills/"):
                parts = link.strip("/").split("/")
                if len(parts) >= 2:
                    links.add(f"/skills/{parts[1]}/")
    return links


def sidebar_skill_nav(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    nav: dict[str, list[str]] = {}
    if not isinstance(data, list):
        return nav
    for item in data:
        if not isinstance(item, dict):
            continue
        direct_link = item.get("link")
        if isinstance(direct_link, str) and direct_link == "/skills/":
            continue
        child_items = item.get("items", [])
        if not isinstance(child_items, list):
            continue
        skill_slug: str | None = None
        titles: list[str] = []
        for child in child_items:
            if not isinstance(child, dict):
                continue
            link = child.get("link")
            title = child.get("text")
            if isinstance(link, str) and link.startswith("/skills/"):
                parts = link.strip("/").split("/")
                if len(parts) >= 2:
                    skill_slug = skill_slug or parts[1]
            if isinstance(title, str):
                titles.append(title)
        if skill_slug:
            nav[skill_slug] = titles
    return nav


def validate_required_skill_nav(root: Path, skills: dict[str, dict[str, str]], errors: list[str]) -> None:
    for name, data in skills.items():
        skill_path = data.get("path", "").replace("\\", "/")
        if not skill_path:
            continue
        manifest_path = root / skill_path / DOCS_MANIFEST_NAME
        if not manifest_path.is_file():
            errors.append(f"{skill_path} 缺少 {DOCS_MANIFEST_NAME}")
            continue
        manifest = parse_subrepo_docs_manifest(manifest_path.read_text(encoding="utf-8"))
        nav = manifest.get("nav", [])
        nav_titles = [
            item.get("title")
            for item in nav
            if isinstance(item, dict) and isinstance(item.get("title"), str)
        ]
        missing = [title for title in REQUIRED_SKILL_NAV_TITLES if title not in nav_titles]
        if missing:
            errors.append(f"{skill_path}/{DOCS_MANIFEST_NAME} 缺少必选资料导航项：")
            errors.extend(f"  - {title}" for title in missing)


def validate_link_surface(
    label: str,
    actual_links: set[str],
    expected_links_by_name: dict[str, str],
    errors: list[str],
) -> None:
    expected_links = set(expected_links_by_name.values())
    missing = sorted(expected_links - actual_links)
    extra = sorted(
        link
        for link in actual_links - expected_links
        if link.startswith("/skills/") and link != "/skills/"
    )
    if missing:
        errors.append(f"{label} 缺少 skill 链接：")
        errors.extend(f"  - {link}" for link in missing)
    if extra:
        errors.append(f"{label} 包含未登记 skill 链接：")
        errors.extend(f"  - {link}" for link in extra)


def main() -> int:
    root = repo_root()
    errors: list[str] = []

    manifest_path = root / MANIFEST_PATH
    if not manifest_path.is_file():
        print(f"缺少 {MANIFEST_PATH.as_posix()}")
        return 1

    skills = parse_skill_docs_manifest(manifest_path.read_text(encoding="utf-8"))
    if not skills:
        print(f"{MANIFEST_PATH.as_posix()} 缺少可读取的 skills 区段。")
        return 1

    manifest_paths = {
        data.get("path", "").replace("\\", "/") for data in skills.values() if data.get("path")
    }
    actual_paths = repo_skill_paths(root)
    missing_manifest_paths = sorted(actual_paths - manifest_paths)
    stale_manifest_paths = sorted(manifest_paths - actual_paths)
    if missing_manifest_paths:
        errors.append("以下 skills/* 子仓缺少 docs/skill-docs.yml 登记：")
        errors.extend(f"  - {path}" for path in missing_manifest_paths)
    if stale_manifest_paths:
        errors.append("docs/skill-docs.yml 登记了不存在的 skills/* 子仓：")
        errors.extend(f"  - {path}" for path in stale_manifest_paths)

    expected_links = expected_skill_links(skills)
    if len(expected_links) != len(skills):
        errors.append("docs/skill-docs.yml 中存在缺少 docs/skills mount 的 skill。")
    validate_required_skill_nav(root, skills, errors)

    home_path = root / HOME_INDEX_PATH
    if not home_path.is_file():
        errors.append(f"缺少 {HOME_INDEX_PATH.as_posix()}")
    else:
        home_section = home_skill_section(home_path.read_text(encoding="utf-8"))
        if not home_section:
            errors.append(f"{HOME_INDEX_PATH.as_posix()} 缺少“当前支持的 Skills”区块。")
        else:
            validate_link_surface(
                HOME_INDEX_PATH.as_posix(),
                {normalize_site_link(link) for link in markdown_links(home_section)},
                expected_links,
                errors,
            )

    skill_index_path = root / SKILL_INDEX_PATH
    if not skill_index_path.is_file():
        errors.append(f"缺少 {SKILL_INDEX_PATH.as_posix()}")
    else:
        validate_link_surface(
            SKILL_INDEX_PATH.as_posix(),
            {normalize_site_link(link) for link in markdown_links(skill_index_path.read_text(encoding="utf-8"))},
            expected_links,
            errors,
        )

    sidebar_path = root / SIDEBAR_PATH
    if not sidebar_path.is_file():
        errors.append(f"缺少 {SIDEBAR_PATH.as_posix()}；请运行 python scripts/sync_skill_docs.py")
    else:
        validate_link_surface(
            SIDEBAR_PATH.as_posix(),
            sidebar_skill_links(sidebar_path),
            expected_links,
            errors,
        )
        sidebar_nav = sidebar_skill_nav(sidebar_path)
        for name, link in expected_links.items():
            skill_slug = link.strip("/").split("/")[-1]
            nav_titles = sidebar_nav.get(skill_slug, [])
            missing = [title for title in REQUIRED_SKILL_NAV_TITLES if title not in nav_titles]
            if missing:
                errors.append(f"{SIDEBAR_PATH.as_posix()} 中 {name} 缺少必选资料导航项：")
                errors.extend(f"  - {title}" for title in missing)

    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"Docs skill surfaces check passed for {len(expected_links)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
