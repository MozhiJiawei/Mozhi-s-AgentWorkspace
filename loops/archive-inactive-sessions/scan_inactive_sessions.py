"""Read-only discovery of inactive Codex sessions across registered local projects."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BEIJING = timezone(timedelta(hours=8), name="Asia/Shanghai")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--inactive-days", type=int, default=7)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    return parser.parse_args()


def load_projects(path: Path) -> dict[str, dict[str, str]]:
    ensure_projects_file(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    projects = payload.get("projects") if isinstance(payload, dict) else payload
    if not isinstance(projects, list):
        raise ValueError("projects file must contain an array or an object with a projects array")
    result: dict[str, dict[str, str]] = {}
    for project in projects:
        if not isinstance(project, dict):
            raise ValueError("every project must be an object")
        if project.get("projectKind") not in (None, "local") or project.get("hostId") not in (None, "local"):
            continue
        project_path = project.get("path")
        project_id = project.get("projectId")
        if not isinstance(project_path, str) or not project_path or not isinstance(project_id, str) or not project_id:
            raise ValueError("every local project needs a nonempty path and projectId")
        result[os.path.normcase(os.path.normpath(project_path))] = {
            "project": project.get("label") or project_path,
            "projectId": project_id,
            "cwd": project_path,
        }
    return result


def ensure_projects_file(path: Path) -> None:
    """Fail clearly when the agent forgot to create the project inventory."""
    if not path.is_file():
        raise FileNotFoundError(
            f"projects file does not exist: {path}; create it from list_projects first"
        )


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def last_event(path: Path) -> datetime | None:
    """Expand the tail until complete records with timestamps are available."""
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            end = handle.tell()
            length = 65536
            while True:
                start = max(0, end - length)
                handle.seek(start)
                lines = handle.read().decode("utf-8", errors="replace").splitlines()
                if start:
                    lines = lines[1:]
                for line in reversed(lines):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    stamp = parse_timestamp(record.get("timestamp")) if isinstance(record, dict) else None
                    if stamp:
                        return stamp
                if not start:
                    return None
                length *= 2
    except OSError as exc:
        raise RuntimeError(f"cannot read rollout: {path}") from exc


def read_indexes(codex_home: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """A missing or failed index is not a successful empty scan."""
    indexes = []
    for path, query in [
        (codex_home / "sqlite" / "codex-dev.db", "SELECT thread_id, cwd, display_title, source_updated_at, source_recency_at FROM local_thread_catalog WHERE host_id='local' AND missing_candidate=0"),
        (codex_home / "state_5.sqlite", "SELECT id, cwd, title, updated_at, recency_at, archived FROM threads"),
    ]:
        if not path.is_file():
            raise FileNotFoundError(f"required local thread index does not exist: {path}")
        try:
            connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            try:
                rows = [dict(row) for row in connection.execute(query)]
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise RuntimeError(f"cannot read local thread index: {path}: {exc}") from exc
        indexes.append({row.get("thread_id", row.get("id")): row for row in rows})
    return indexes[0], indexes[1]


def main() -> int:
    args = parse_args()
    if args.inactive_days < 1:
        raise ValueError("--inactive-days must be positive")
    projects = load_projects(args.projects_file)
    cutoff_local = datetime.now(BEIJING) - timedelta(days=args.inactive_days)
    cutoff_utc = cutoff_local.astimezone(timezone.utc)
    sessions_root = args.codex_home / "sessions"
    catalog, state = read_indexes(args.codex_home)
    sessions: dict[str, dict[str, Any]] = {}
    scanned_files = 0
    unreadable_files = 0

    for rollout in sessions_root.rglob("*.jsonl"):
        try:
            with rollout.open("rb") as handle:
                metadata = json.loads(handle.readline().decode("utf-8", errors="ignore")).get(
                    "payload", {}
                )
            if not isinstance(metadata, dict):
                raise ValueError("session metadata is not an object")
        except (OSError, json.JSONDecodeError, AttributeError, ValueError):
            unreadable_files += 1
            continue
        cwd = metadata.get("cwd")
        normalized_cwd = os.path.normcase(os.path.normpath(cwd)) if cwd else ""
        if normalized_cwd not in projects:
            continue
        session_id = metadata.get("id") or metadata.get("session_id")
        if not session_id:
            continue
        scanned_files += 1
        event_time = last_event(rollout) or parse_timestamp(metadata.get("timestamp"))
        if event_time is None:
            unreadable_files += 1
            continue
        current = sessions.get(session_id)
        if current and parse_timestamp(current["last_active_utc"]) >= event_time:
            current["rollout_files"] += 1
            continue
        sessions[session_id] = {
            "id": session_id,
            **projects[normalized_cwd],
            "title": metadata.get("title") or metadata.get("thread_name") or "",
            "thread_source": metadata.get("thread_source"),
            "last_active_utc": event_time.isoformat().replace("+00:00", "Z"),
            "rollout_files": (current or {}).get("rollout_files", 0) + 1,
            "sample_path": str(rollout),
        }

    # SQLite-history threads may have no active rollout file. Catalog cwd also
    # prevents inherited or stale rollout metadata from selecting another project.
    for session_id, entry in catalog.items():
        cwd = entry.get("cwd")
        project = projects.get(os.path.normcase(os.path.normpath(cwd))) if cwd else None
        if not project:
            sessions.pop(session_id, None)
            continue
        row = sessions.setdefault(session_id, {
            "id": session_id, "last_active_utc": None,
            "rollout_files": 0, "sample_path": "", "thread_source": None,
        })
        row.update(project)
        row["title"] = entry["display_title"]
    rows = []
    already_archived = 0
    for row in sessions.values():
        thread_state = state.get(row["id"])
        if thread_state and thread_state["archived"]:
            already_archived += 1
            continue
        times = [parse_timestamp(row["last_active_utc"])]
        for source, keys in [(catalog.get(row["id"]), ("source_updated_at", "source_recency_at")), (thread_state, ("updated_at", "recency_at"))]:
            if source:
                times.extend(datetime.fromtimestamp(source[key], timezone.utc) for key in keys if source.get(key))
        last_active = max((stamp for stamp in times if stamp), default=None)
        if last_active is None:
            raise ValueError(f"no last-active timestamp for local thread {row['id']}")
        row["last_active_utc"] = last_active.isoformat().replace("+00:00", "Z")
        row["eligible"] = bool(last_active and last_active < cutoff_utc)
        row["addressable"] = row["id"] in catalog and thread_state is not None
        if row["eligible"]:
            rows.append(row)
    if unreadable_files:
        raise RuntimeError(f"scan incomplete: {unreadable_files} rollout files have unreadable metadata or timestamps; no candidates written")
    rows.sort(key=lambda row: row["last_active_utc"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidates = [row for row in rows if row["addressable"]]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cutoff_local": cutoff_local.isoformat(),
        "cutoff_utc": cutoff_utc.isoformat().replace("+00:00", "Z"),
        "scanned_projects": len(projects),
        "scanned_rollout_files": scanned_files,
        "unique_sessions": len(sessions),
        "already_archived_sessions": already_archived,
        "eligible_sessions": len(rows),
        "addressable_candidates": len(candidates),
        "local_only_eligible": len(rows) - len(candidates),
        "candidates": candidates,
        "local_only": [row for row in rows if not row["addressable"]],
    }
    (args.output_dir / "candidates.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    fields = ["id", "project", "projectId", "cwd", "title", "thread_source", "last_active_utc", "rollout_files", "eligible", "addressable", "sample_path"]
    with (args.output_dir / "candidates.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in rows)
    summary = {key: value for key, value in payload.items() if key not in ("candidates", "local_only")}
    summary["by_project"] = {project["projectId"]: {
        "label": project["project"],
        "addressable_candidates": sum(row["projectId"] == project["projectId"] for row in candidates),
        "local_only_eligible": sum(row["projectId"] == project["projectId"] and not row["addressable"] for row in rows),
    } for project in projects.values()}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
