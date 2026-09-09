from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_state
import task_api


class WorkRootCLITests(unittest.TestCase):
    def test_missing_relative_and_nonexistent_roots_fail_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            for module, command in (
                (local_state, ["lock", "acquire"]),
                (local_state, ["filter"]),
                (local_state, ["list"]),
                (task_api, ["fetch"]),
            ):
                for prefix in (
                    [],
                    ["--work-root", "relative-root"],
                    ["--work-root", str(Path(directory) / "missing")],
                ):
                    with self.subTest(module=module.__name__, prefix=prefix, command=command):
                        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                            module.build_parser().parse_args(prefix + command)
                        self.assertEqual(error.exception.code, 2)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_fetch_filter_complete_and_lock_share_one_work_root(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            work = Path(directory) / "work with spaces"
            work.mkdir()
            root = work / "loop-ccn-brief-report"
            prefix = ["--work-root", str(work)]
            lock = local_state.build_parser().parse_args(prefix + ["lock", "acquire"])
            lock.func(lock)
            self.assertTrue((root / "run.lock").is_file())
            with self.assertRaises(RuntimeError):
                lock.func(lock)

            fetch = task_api.build_parser().parse_args(prefix + ["fetch"])
            with patch.object(task_api, "load_config", return_value={}), patch.object(
                task_api, "load_credentials", return_value={}
            ), patch.object(task_api, "api_base", return_value="https://example.test"), patch.object(
                task_api, "api_key", return_value="test-key"
            ), patch.object(task_api, "fetch_tasks", return_value=[{"task_id": "TASK-1"}]):
                fetch.func(fetch)

            queue = local_state.build_parser().parse_args(
                prefix + ["filter", "--ccn-root", str(work / "archive")]
            )
            queue.func(queue)
            self.assertEqual(json.loads((root / "pending.json").read_text())[0]["task_id"], "TASK-1")
            self.assertEqual(json.loads((root / "rejected-tasks.json").read_text()), [])

            report = work / "archive"
            report.mkdir()
            (report / "Example.html").write_text("html", encoding="utf-8")
            (report / "Example.pptx").write_bytes(b"pptx")
            complete = task_api.build_parser().parse_args(prefix + [
                "complete", "--task-id", "TASK-1", "--artifact-url", "https://example.test/tree/main/archive",
                "--html-download-url", "https://example.test/Example.html",
                "--pptx-download-url", "https://example.test/Example.pptx",
                "--report-path", str(report),
            ])
            with patch.object(task_api, "load_config", return_value={}), patch.object(
                task_api, "load_credentials", return_value={}
            ), patch.object(task_api, "api_base", return_value="https://example.test"), patch.object(
                task_api, "api_key", return_value="test-key"
            ), patch.object(task_api, "validate_artifact_url", side_effect=lambda value, _: value), patch.object(
                task_api, "validate_download_url", side_effect=lambda value, *args, **kwargs: value
            ), patch.object(task_api, "validate_completion_report", return_value="Example"), patch.object(
                task_api, "submit_result", return_value={"status": "completed"}
            ), patch.object(task_api, "fetch_task", return_value={"category": None}), patch.object(
                task_api, "DEFAULT_CCN_ROOT", work
            ), patch.object(task_api, "load_config", return_value={"ccn_report_repository_url":"https://example.test"}
            ):
                complete.func(complete)
            self.assertEqual(local_state.load_state(root / "state.json")["tasks"]["TASK-1"]["status"], "archived")
            release = local_state.build_parser().parse_args(prefix + ["lock", "release"])
            release.func(release)
            self.assertFalse((root / "run.lock").exists())
            self.assertEqual({item.name for item in root.iterdir()}, {
                "tasks.json", "rejected-tasks.json", "pending.json", "state.json"
            })
            self.assertEqual({item.name for item in work.iterdir()}, {"loop-ccn-brief-report", "archive"})

    def test_missing_queue_is_not_treated_as_no_pending_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            args = local_state.build_parser().parse_args(["--work-root", directory, "filter"])
            with self.assertRaises(FileNotFoundError):
                args.func(args)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
