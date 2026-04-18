from __future__ import annotations

import configparser
from collections import Counter
from pathlib import Path
import re
import sys


def parse_gitmodules(gitmodules_path: Path) -> list[str]:
    parser = configparser.ConfigParser()
    parser.read(gitmodules_path, encoding="utf-8")
    paths: list[str] = []
    for section in parser.sections():
        if parser.has_option(section, "path"):
            path = parser.get(section, "path").strip()
            if path.startswith("skills/"):
                paths.append(path)
    return sorted(paths)


def parse_registered_skills(agents_path: Path) -> list[str]:
    text = agents_path.read_text(encoding="utf-8")
    return re.findall(r"^### `([^`]+)`$", text, flags=re.MULTILINE)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    gitmodules_path = root / ".gitmodules"
    agents_path = root / "AGENTS.md"

    if not gitmodules_path.exists():
        print("Missing .gitmodules")
        return 1

    if not agents_path.exists():
        print("Missing AGENTS.md")
        return 1

    submodule_skills = parse_gitmodules(gitmodules_path)
    registered_skills = parse_registered_skills(agents_path)

    submodule_counts = Counter(submodule_skills)
    registered_counts = Counter(registered_skills)

    duplicate_submodules = sorted(path for path, count in submodule_counts.items() if count > 1)
    duplicate_registered = sorted(path for path, count in registered_counts.items() if count > 1)

    submodule_set = set(submodule_skills)
    registered_set = set(registered_skills)

    missing = sorted(path for path in submodule_set if path not in registered_set)
    orphaned = sorted(path for path in registered_set if path.startswith("skills/") and path not in submodule_set)

    if duplicate_submodules:
        print("Duplicate skill paths found in .gitmodules:")
        for path in duplicate_submodules:
            print(f"  - {path}")

    if duplicate_registered:
        print("Duplicate skill registrations found in AGENTS.md:")
        for path in duplicate_registered:
            print(f"  - {path}")

    if missing:
        print("Skills present in .gitmodules but not registered in AGENTS.md:")
        for path in missing:
            print(f"  - {path}")

    if orphaned:
        print("Skills registered in AGENTS.md but missing from .gitmodules:")
        for path in orphaned:
            print(f"  - {path}")

    if duplicate_submodules or duplicate_registered or missing or orphaned:
        return 1

    print(f"Registry check passed for {len(submodule_set)} skill submodule(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
