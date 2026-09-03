from __future__ import annotations

import subprocess
import sys
from pathlib import Path


LOOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOOP_ROOT))

from check_temp_directories import audit_workspace, check_tmp_layout  # noqa: E402


WORKSPACE_GITIGNORE = LOOP_ROOT.parents[1] / ".gitignore"


def init_repository(path: Path) -> None:
    subprocess.run(["git", "init", "--quiet", str(path)], check=True)


def write_policy_gitignore(path: Path) -> None:
    (path / ".gitignore").write_text(
        WORKSPACE_GITIGNORE.read_text(encoding="utf-8"), encoding="utf-8"
    )


def make_valid_tmp(path: Path) -> None:
    (path / ".tmp" / "runs").mkdir(parents=True)
    (path / ".tmp" / "retained").mkdir()
    (path / ".tmp" / "README.md").write_text("runtime\n", encoding="utf-8")


def test_gitignore_hash_must_match_before_directory_scan(tmp_path: Path) -> None:
    init_repository(tmp_path)
    make_valid_tmp(tmp_path)
    (tmp_path / ".gitignore").write_text("modified\n", encoding="utf-8")
    (tmp_path / "extra-output").mkdir()

    findings, errors, skipped = audit_workspace(tmp_path)
    assert errors == []
    assert skipped is True
    assert any("hash differs from the approved Loop baseline" in item["problem"] for item in findings)
    assert all(item["check"] != "git-directory" for item in findings)


def test_git_reports_untracked_directory_after_gitignore_is_valid(tmp_path: Path) -> None:
    init_repository(tmp_path)
    make_valid_tmp(tmp_path)
    write_policy_gitignore(tmp_path)
    (tmp_path / "extra-output").mkdir()
    (tmp_path / "extra-output" / "result.txt").write_text("x", encoding="utf-8")

    findings, errors, skipped = audit_workspace(tmp_path)

    assert errors == []
    assert skipped is False
    assert {
        "check": "git-directory",
        "path": "extra-output",
        "problem": "untracked directory requiring classification",
    } in findings


def test_allowed_ignored_directories_are_not_reported(tmp_path: Path) -> None:
    init_repository(tmp_path)
    make_valid_tmp(tmp_path)
    write_policy_gitignore(tmp_path)
    for relative in (
        ".tmp_old/archive",
        "node_modules/package",
        "src/__pycache__",
        "tests/.pytest_cache",
        "docs/.vitepress/cache",
        "docs/.vitepress/dist",
        "docs/.vitepress/generated",
        "docs/skills",
        "docs/public/material-quality",
        "docs/public/skill-static",
    ):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/public/material-quality/generated.txt").write_text(
        "generated", encoding="utf-8"
    )
    (tmp_path / "docs/public/skill-static/generated.txt").write_text(
        "generated", encoding="utf-8"
    )

    findings, errors, skipped = audit_workspace(tmp_path)

    assert errors == []
    assert skipped is False
    assert findings == []


def test_tmp_layout_checks_run_id_root_entries_and_direct_files(tmp_path: Path) -> None:
    make_valid_tmp(tmp_path)
    (tmp_path / ".tmp" / "unexpected.txt").write_text("x", encoding="utf-8")
    (tmp_path / ".tmp" / "runs" / "bad-name").mkdir()
    (tmp_path / ".tmp" / "runs" / "loose.log").write_text("x", encoding="utf-8")
    (tmp_path / ".tmp" / "retained" / "loose.log").write_text("x", encoding="utf-8")

    findings = check_tmp_layout(tmp_path)
    paths = {item["path"] for item in findings}

    assert ".tmp/unexpected.txt" in paths
    assert ".tmp/runs/bad-name" in paths
    assert ".tmp/runs/loose.log" in paths
    assert ".tmp/retained/loose.log" in paths


def test_tmp_layout_detects_same_work_in_runs_and_retained(tmp_path: Path) -> None:
    make_valid_tmp(tmp_path)
    (tmp_path / ".tmp" / "runs" / "20260903-163000-demo").mkdir()
    (tmp_path / ".tmp" / "retained" / "demo").mkdir()

    findings = check_tmp_layout(tmp_path)

    assert any("same work also exists" in item["problem"] for item in findings)


def test_valid_tmp_layout_passes(tmp_path: Path) -> None:
    make_valid_tmp(tmp_path)
    (tmp_path / ".tmp" / "runs" / "20260903-163000-one-off").mkdir()
    (tmp_path / ".tmp" / "retained" / "长期工作").mkdir()

    assert check_tmp_layout(tmp_path) == []
