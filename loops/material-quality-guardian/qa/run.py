from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

from common import repo_root


DEFAULT_OUTPUT_ROOT = Path(".tmp/loops/material-quality-guardian")


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str]


def run_check(root: Path, check: Check) -> int:
    print(f"[qa] {check.name}")
    result = subprocess.run(check.command, cwd=root)
    if result.returncode != 0:
        print(f"[fail] {check.name}")
        return result.returncode
    print(f"[pass] {check.name}")
    return 0


def local_checks() -> list[Check]:
    qa_root = Path(__file__).resolve().parent
    return [
        Check("agents-registry", [sys.executable, str(qa_root / "check_agents_registry.py")]),
        Check(
            "readme-skill-prompts",
            [sys.executable, str(qa_root / "check_readme_skill_prompts.py")],
        ),
        Check(
            "skill-dependencies",
            [sys.executable, str(qa_root / "check_skill_dependencies.py")],
        ),
        Check("skill-docs", [sys.executable, str(qa_root / "check_skill_docs.py")]),
        Check(
            "docs-skill-surfaces",
            [sys.executable, str(qa_root / "check_docs_skill_surfaces.py")],
        ),
        Check(
            "docs-publish-state",
            [sys.executable, str(qa_root / "check_docs_publish_state.py")],
        ),
    ]


def remote_checks(output_root: Path) -> list[Check]:
    qa_root = Path(__file__).resolve().parent
    return [
        Check(
            "remote-docs-publish",
            [
                sys.executable,
                str(qa_root / "audit_remote_docs_publish.py"),
                "--output",
                str(output_root / "remote-publish-audit.json"),
                "--fail-on-drift",
            ],
        ),
        Check(
            "remote-rendered-docs",
            [
                sys.executable,
                str(qa_root / "audit_remote_rendered_docs.py"),
                "--output",
                str(output_root / "remote-rendered-audit.json"),
                "--fail-on-broken",
            ],
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Material Quality Guardian QA checks.")
    parser.add_argument(
        "--include-remote",
        action="store_true",
        help="Also run remote docs publish/render audits.",
    )
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT.as_posix(),
        help="Output directory for remote audit JSON artifacts.",
    )
    args = parser.parse_args()

    root = repo_root()
    output_root = (root / args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    checks = local_checks()
    if args.include_remote:
        checks.extend(remote_checks(output_root))

    failed = 0
    for check in checks:
        code = run_check(root, check)
        if code != 0:
            failed = failed or code

    if failed:
        print("[fail] material quality QA")
        return failed
    print("[pass] material quality QA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
