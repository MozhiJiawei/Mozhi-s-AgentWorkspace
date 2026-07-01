from __future__ import annotations

from pathlib import Path
import re
import sys


README_SECTION_TITLE = "## Skill Prompt 示例"


def parse_registered_skills(agents_path: Path) -> list[str]:
    text = agents_path.read_text(encoding="utf-8")
    return re.findall(r"^### `([^`]+)`$", text, flags=re.MULTILINE)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    readme_path = root / "README.md"
    agents_path = root / "AGENTS.md"

    if not readme_path.exists():
        print("Missing README.md")
        return 1

    if not agents_path.exists():
        print("Missing AGENTS.md")
        return 1

    readme_text = readme_path.read_text(encoding="utf-8")
    registered_skills = parse_registered_skills(agents_path)

    errors: list[str] = []

    if README_SECTION_TITLE not in readme_text:
        errors.append(f"README.md is missing required section: {README_SECTION_TITLE}")

    for skill_path in registered_skills:
        skill_heading = f"### `{skill_path}`"
        if skill_heading not in readme_text:
            errors.append(f"README.md is missing prompt examples for skill: {skill_path}")

    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"README skill prompt examples check passed for {len(registered_skills)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
