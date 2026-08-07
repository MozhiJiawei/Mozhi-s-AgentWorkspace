from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest


LOOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOOP_ROOT))

import local_state  # noqa: E402


class LocalStateTests(unittest.TestCase):
    def test_archive_scan_finds_task_id_in_readme(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "大厂动态" / "Example" / "20260803-example-codex"
            report.mkdir(parents=True)
            (report / "README.md").write_text("# Report\n\n- 任务编号：`TASK-20260803-01`\n", encoding="utf-8")

            found = local_state.task_ids_in_archive(root)

            self.assertEqual(str(report.resolve()), found["TASK-20260803-01"])

    def test_filter_keeps_api_pending_and_marks_local_report_for_delivery_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ccn_root = root / "ccn-report"
            report = ccn_root / "type" / "project" / "20260803-example-codex"
            report.mkdir(parents=True)
            (report / "README.md").write_text("任务编号：TASK-1\n", encoding="utf-8")
            tasks_path = root / "tasks.json"
            output_path = root / "pending.json"
            state_path = root / "state.json"
            tasks_path.write_text(
                json.dumps([{"task_id": "TASK-1"}, {"task_id": "TASK-2"}]),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                tasks=str(tasks_path),
                output=str(output_path),
                ccn_root=str(ccn_root),
                state=str(state_path),
            )

            local_state.cmd_filter(args)

            queued = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(["TASK-1", "TASK-2"], [task["task_id"] for task in queued])
            self.assertEqual("delivery", queued[0]["resume_from"])
            self.assertEqual(str(report.resolve()), queued[0]["local_report_path"])
            self.assertEqual("generation", queued[1]["resume_from"])

    def test_completed_task_is_recoverable_from_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report"
            report.mkdir()
            state_path = root / "state.json"

            record = local_state.record_completed_task(
                state_path,
                task_id="TASK-1",
                report_path=str(report),
                artifact_url="https://example.test/report",
            )

            state = local_state.load_state(state_path)
            found = local_state.archived_task_ids(state, root / "missing-ccn")

            self.assertEqual("archived", record["status"])
            self.assertEqual(str(report.resolve()), found["TASK-1"])

    def test_parser_does_not_expose_manual_mark_command(self):
        with self.assertRaises(SystemExit):
            local_state.build_parser().parse_args(["mark"])

    def test_lock_rejects_active_lock_and_recovers_stale_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "run.lock"
            local_state.acquire_lock(lock, stale_hours=20)
            with self.assertRaises(RuntimeError):
                local_state.acquire_lock(lock, stale_hours=20)

            lock.write_text(
                json.dumps({"created_at": "2000-01-01T00:00:00+00:00"}),
                encoding="utf-8",
            )
            recovered = local_state.acquire_lock(lock, stale_hours=20)
            self.assertIn("created_at", recovered)


if __name__ == "__main__":
    unittest.main()
