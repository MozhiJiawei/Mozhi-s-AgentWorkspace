from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


LOOP_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = LOOP_ROOT.parent.parent
RUNTIME_ROOT = WORKSPACE_ROOT / ".tmp" / "loops" / "ccn-brief-report"
DEFAULT_STATE = RUNTIME_ROOT / "state.json"
DEFAULT_LOCK = RUNTIME_ROOT / "run.lock"
DEFAULT_CONFIG = LOOP_ROOT / "config.json"
DEFAULT_CCN_ROOT = WORKSPACE_ROOT / "ccn-report"
TASK_ID_PATTERN = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:task[_ ]?id|任务编号)\s*[:：]\s*`?([A-Za-z0-9._-]+)`?\s*$"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def load_state(path: Path) -> dict[str, Any]:
    payload = read_json(path, {"version": 1, "tasks": {}})
    if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), dict):
        raise ValueError("状态文件格式无效")
    payload.setdefault("version", 1)
    return payload


def task_ids_in_archive(ccn_root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    if not ccn_root.exists():
        return found
    for readme in ccn_root.rglob("README.md"):
        try:
            relative = readme.relative_to(ccn_root)
        except ValueError:
            continue
        if any(part in {".git", ".tmp", "node_modules"} for part in relative.parts):
            continue
        try:
            text = readme.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for match in TASK_ID_PATTERN.finditer(text):
            found.setdefault(match.group(1), str(readme.parent.resolve()))
    return found


def archived_task_ids(state: dict[str, Any], ccn_root: Path) -> dict[str, str]:
    found = task_ids_in_archive(ccn_root)
    for task_id, record in state["tasks"].items():
        if record.get("status") == "archived" and record.get("report_path"):
            report_path = Path(record["report_path"])
            if report_path.exists():
                found.setdefault(task_id, str(report_path.resolve()))
    return found


def acquire_lock(lock_path: Path, stale_hours: float) -> dict[str, Any]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        existing = read_json(lock_path, {})
        created_raw = existing.get("created_at") if isinstance(existing, dict) else None
        try:
            created_at = datetime.fromisoformat(created_raw)
        except (TypeError, ValueError):
            created_at = utc_now()
        if utc_now() - created_at <= timedelta(hours=stale_hours):
            raise RuntimeError(f"Loop 已有活动锁：{lock_path}")
        lock_path.unlink()
    payload = {"pid": os.getpid(), "created_at": iso_now()}
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"Loop 已有活动锁：{lock_path}") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return payload


def cmd_lock(args: argparse.Namespace) -> int:
    lock_path = Path(args.lock).resolve()
    if args.action == "acquire":
        config = read_json(Path(args.config), {})
        stale_hours = float(config.get("run_lock_stale_hours", 20))
        print(json.dumps(acquire_lock(lock_path, stale_hours), ensure_ascii=False))
    else:
        if lock_path.exists():
            lock_path.unlink()
        print(json.dumps({"released": str(lock_path)}, ensure_ascii=False))
    return 0


def cmd_filter(args: argparse.Namespace) -> int:
    tasks = read_json(Path(args.tasks), [])
    if not isinstance(tasks, list):
        raise ValueError("任务文件必须是数组")
    state = load_state(Path(args.state))
    local_reports = archived_task_ids(state, Path(args.ccn_root).resolve())
    pending = []
    resumed = []
    for raw_task in tasks:
        task = dict(raw_task)
        task_id = str(task.get("task_id"))
        report_path = local_reports.get(task_id)
        if report_path:
            task["resume_from"] = "delivery"
            task["local_report_path"] = report_path
            resumed.append(task_id)
        else:
            task["resume_from"] = "generation"
        pending.append(task)
    output = Path(args.output).resolve()
    write_json_atomic(output, pending)
    print(
        json.dumps(
            {
                "pending": len(pending),
                "resumed": len(resumed),
                "resumed_task_ids": resumed,
                "output": str(output),
            },
            ensure_ascii=False,
        )
    )
    return 0


def record_completed_task(
    path: Path,
    *,
    task_id: str,
    report_path: str,
    artifact_url: str,
) -> dict[str, Any]:
    state = load_state(path)
    current = state["tasks"].get(task_id, {})
    record = {
        **current,
        "task_id": task_id,
        "status": "archived",
        "updated_at": iso_now(),
        "report_path": str(Path(report_path).resolve()),
        "artifact_url": artifact_url,
    }
    record.pop("error", None)
    state["tasks"][task_id] = record
    write_json_atomic(path, state)
    return record


def cmd_list(args: argparse.Namespace) -> int:
    print(json.dumps(load_state(Path(args.state)), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="维护 CCN 快报 Loop 的本地调测状态与去重信息。")
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    subparsers = parser.add_subparsers(dest="command", required=True)

    lock_parser = subparsers.add_parser("lock")
    lock_parser.add_argument("action", choices=["acquire", "release"])
    lock_parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    lock_parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    lock_parser.set_defaults(func=cmd_lock)

    filter_parser = subparsers.add_parser("filter")
    filter_parser.add_argument("--tasks", required=True)
    filter_parser.add_argument("--output", required=True)
    filter_parser.add_argument("--ccn-root", default=str(DEFAULT_CCN_ROOT))
    filter_parser.set_defaults(func=cmd_filter)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(func=cmd_list)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
