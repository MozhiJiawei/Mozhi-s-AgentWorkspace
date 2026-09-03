from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


LOOP_ROOT = Path(__file__).resolve().parent
GITIGNORE_HASH = LOOP_ROOT / "gitignore.sha256"
TMP_ROOT_ENTRIES = {"README.md", "runs", "retained"}
RUN_ID = re.compile(r"^(\d{8})-(\d{6})-(.+)$")


def issue(check: str, path: str, problem: str) -> dict[str, str]:
    return {"check": check, "path": path, "problem": problem}


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def canonical_sha256(path: Path) -> str:
    canonical_text = path.read_text(encoding="utf-8")
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def check_gitignore(workspace: Path) -> tuple[list[dict[str, str]], bool]:
    path = workspace / ".gitignore"
    if not path.is_file():
        return [issue("gitignore", ".gitignore", "missing current file")], False
    if not GITIGNORE_HASH.is_file():
        return [issue("gitignore", str(GITIGNORE_HASH), "missing baseline hash")], False

    expected_hash = GITIGNORE_HASH.read_text(encoding="ascii").strip().casefold()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        return [issue("gitignore", str(GITIGNORE_HASH), "invalid SHA-256 value")], False
    if canonical_sha256(path) != expected_hash:
        return [
            issue(
                "gitignore",
                ".gitignore",
                "hash differs from the approved Loop baseline; review the change",
            )
        ], False

    return [], True


def discover_repositories(workspace: Path) -> tuple[list[Path], list[str]]:
    command = ["git", "-C", str(workspace), "submodule", "foreach", "--recursive", "--quiet", "pwd"]
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        return [workspace], [f"git submodule discovery failed: {detail}"]

    repositories = [workspace]
    for raw_line in completed.stdout.decode("utf-8", errors="replace").splitlines():
        value = raw_line.strip()
        if os.name == "nt" and re.match(r"^/[A-Za-z]/", value):
            value = f"{value[1]}:/{value[3:]}"
        candidate = Path(value).resolve()
        if candidate.is_dir() and candidate not in repositories:
            repositories.append(candidate)
    return repositories, []


def git_untracked_directories(repository: Path) -> tuple[list[Path], str | None]:
    command = [
        "git",
        "-C",
        str(repository),
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
        "--ignored=no",
        "-z",
    ]
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        return [], f"git status scan failed for {repository}: {detail}"

    directories: list[Path] = []
    for raw_record in completed.stdout.split(b"\0"):
        if not raw_record.startswith(b"?? "):
            continue
        relative = raw_record[3:].decode("utf-8", errors="surrogateescape")
        candidate = (repository / relative).resolve()
        if candidate.is_dir():
            directories.append(candidate)
    return directories, None


def collapse_directory_findings(
    findings: dict[Path, set[str]], workspace: Path
) -> list[dict[str, str]]:
    collapsed: dict[Path, set[str]] = {}
    for path in sorted(findings, key=lambda item: (len(item.parts), str(item).casefold())):
        parent = next((item for item in collapsed if is_within(path, item)), None)
        if parent is None:
            collapsed[path] = set(findings[path])
        else:
            collapsed[parent].update(findings[path])

    records: list[dict[str, str]] = []
    for path, reasons in sorted(collapsed.items(), key=lambda item: str(item[0]).casefold()):
        relative = path.relative_to(workspace).as_posix()
        records.append(issue("git-directory", relative, ", ".join(sorted(reasons))))
    return records


def check_git_directories(
    workspace: Path,
) -> tuple[list[dict[str, str]], list[str]]:
    repositories, errors = discover_repositories(workspace)
    findings: dict[Path, set[str]] = defaultdict(set)

    for repository in repositories:
        untracked_directories, error = git_untracked_directories(repository)
        if error:
            errors.append(error)
        else:
            for directory in untracked_directories:
                findings[directory].add("untracked directory requiring classification")

    return collapse_directory_findings(findings, workspace), errors


def valid_run_id(name: str) -> bool:
    match = RUN_ID.fullmatch(name)
    if not match:
        return False
    try:
        datetime.strptime(f"{match.group(1)}-{match.group(2)}", "%Y%m%d-%H%M%S")
    except ValueError:
        return False
    return bool(match.group(3).strip())


def check_tmp_layout(workspace: Path) -> list[dict[str, str]]:
    tmp_root = workspace / ".tmp"
    findings: list[dict[str, str]] = []
    if not tmp_root.is_dir():
        return [issue("tmp-layout", ".tmp", "missing Workspace temporary root")]

    for entry in sorted(tmp_root.iterdir(), key=lambda item: item.name.casefold()):
        if entry.name not in TMP_ROOT_ENTRIES:
            findings.append(
                issue("tmp-layout", f".tmp/{entry.name}", "unexpected entry at .tmp root")
            )

    runs = tmp_root / "runs"
    retained = tmp_root / "retained"
    for path, label in ((runs, "runs"), (retained, "retained")):
        if not path.is_dir():
            findings.append(issue("tmp-layout", f".tmp/{label}", "missing required directory"))

    run_names: dict[str, str] = {}
    if runs.is_dir():
        for entry in sorted(runs.iterdir(), key=lambda item: item.name.casefold()):
            if entry.name == ".gitkeep" and entry.is_file():
                continue
            if not entry.is_dir():
                findings.append(
                    issue(
                        "tmp-layout",
                        f".tmp/runs/{entry.name}",
                        "runs may contain only .gitkeep and run-root directories",
                    )
                )
                continue
            if not valid_run_id(entry.name):
                findings.append(
                    issue(
                        "tmp-layout",
                        f".tmp/runs/{entry.name}",
                        "run root must use YYYYMMDD-HHMMSS-<short-name>",
                    )
                )
                continue
            short_name = RUN_ID.fullmatch(entry.name).group(3)
            run_names[short_name.casefold()] = entry.name

    retained_names: dict[str, str] = {}
    if retained.is_dir():
        for entry in sorted(retained.iterdir(), key=lambda item: item.name.casefold()):
            if entry.name == ".gitkeep" and entry.is_file():
                continue
            if not entry.is_dir():
                findings.append(
                    issue(
                        "tmp-layout",
                        f".tmp/retained/{entry.name}",
                        "retained may contain only .gitkeep and work-root directories",
                    )
                )
                continue
            retained_names[entry.name.casefold()] = entry.name

    for name in sorted(run_names.keys() & retained_names.keys()):
        findings.append(
            issue(
                "tmp-layout",
                f".tmp/runs/{run_names[name]}",
                f"same work also exists in .tmp/retained/{retained_names[name]}",
            )
        )

    return findings


def audit_workspace(workspace: Path) -> tuple[list[dict[str, str]], list[str], bool]:
    workspace = workspace.resolve()
    gitignore_findings, gitignore_ok = check_gitignore(workspace)
    findings = [*gitignore_findings, *check_tmp_layout(workspace)]
    errors: list[str] = []
    directory_scan_skipped = not gitignore_ok

    if gitignore_ok:
        directory_findings, directory_errors = check_git_directories(workspace)
        findings.extend(directory_findings)
        errors.extend(directory_errors)

    return findings, errors, directory_scan_skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Workspace .gitignore, Git-visible directories, and .tmp layout."
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        print(f"SCAN_ERROR: workspace is not a directory: {workspace}", file=sys.stderr)
        return 2

    findings, errors, directory_scan_skipped = audit_workspace(workspace)
    status = "scan-error" if errors else "violations" if findings else "ok"

    if args.json_output:
        print(
            json.dumps(
                {
                    "workspace": str(workspace),
                    "status": status,
                    "directory_scan_skipped": directory_scan_skipped,
                    "findings": findings,
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if errors:
            print("SCAN_ERROR: the Workspace audit did not complete:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
        if findings:
            print(f"NON_COMPLIANT: found {len(findings)} Workspace hygiene issues:")
            for finding in findings:
                print(
                    f"- [{finding['check']}] {finding['path']}: {finding['problem']}"
                )
        if directory_scan_skipped:
            print("- [git-directory] skipped until .gitignore matches the Loop policy")
        elif not findings and not errors:
            print("OK: .gitignore, Git-visible directories, and .tmp layout are compliant.")

    if errors:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
