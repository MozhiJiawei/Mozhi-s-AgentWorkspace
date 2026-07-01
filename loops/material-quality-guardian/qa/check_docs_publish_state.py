from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from docs_publish_state import ROOT, _iter_workspace_source_files


GENERATED_STATE_PREFIX = "public/material-quality/"
GENERATED_STATE_REPO_PATH = "docs/public/material-quality/publish-state.json"


def git_ls_files(path: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", path],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return [path]
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    tracked_state_files = git_ls_files(GENERATED_STATE_REPO_PATH)
    if tracked_state_files:
        print(
            "[fail] generated publish-state is tracked by git; "
            f"remove it from the index: {GENERATED_STATE_REPO_PATH}",
            file=sys.stderr,
        )
        return 1

    workspace_files = _iter_workspace_source_files(ROOT)
    leaked_files = [
        path.relative_to(ROOT / "docs").as_posix()
        for path in workspace_files
        if path.relative_to(ROOT / "docs").as_posix().startswith(GENERATED_STATE_PREFIX)
    ]
    if leaked_files:
        print(
            "[fail] generated publish-state files are included in docs source fingerprint:",
            file=sys.stderr,
        )
        for rel in leaked_files:
            print(f"  - docs/{rel}", file=sys.stderr)
        return 1

    print("Docs publish-state check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
