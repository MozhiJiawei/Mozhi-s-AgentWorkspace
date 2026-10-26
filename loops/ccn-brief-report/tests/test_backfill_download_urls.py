from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

import requests


LOOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOOP_ROOT))

import backfill_download_urls  # noqa: E402


CONFIG = {"ccn_report_repository_url": "https://github.com/MozhiJiawei/ccn-report"}
API_BASE = "https://ccn-api.example.test"
API_KEY = "test-api-key-" + "x" * 32


class BackfillDownloadUrlsTests(unittest.TestCase):
    def response(self, payload):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        return response

    def test_fetch_returns_more_than_500_completed_tasks_with_one_request(self):
        session = Mock()
        data = [{"task_id": f"TASK-{index}"} for index in range(1, 502)]
        session.get.return_value = self.response({"status": "success", "data": data})

        tasks = backfill_download_urls.fetch_completed_tasks(
            base_url=API_BASE, key=API_KEY, timeout=30, session=session
        )

        self.assertEqual(data, tasks)
        session.get.assert_called_once_with(
            f"{API_BASE}/api/v1/tasks",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"status": "completed"},
            timeout=(5, 30),
        )

    def test_fetch_returns_empty_tasks(self):
        session = Mock()
        session.get.return_value = self.response({"status": "success", "data": []})

        tasks = backfill_download_urls.fetch_completed_tasks(
            base_url=API_BASE, key=API_KEY, timeout=30, session=session
        )

        self.assertEqual([], tasks)
        session.get.assert_called_once()

    def test_fetch_filters_non_objects_and_preserves_duplicate_objects(self):
        session = Mock()
        task = {"task_id": "TASK-1"}
        data = [task, None, "not a task", 2, [], {}, dict(task)]
        session.get.return_value = self.response({"status": "success", "data": data})

        tasks = backfill_download_urls.fetch_completed_tasks(
            base_url=API_BASE, key=API_KEY, timeout=30, session=session
        )

        self.assertEqual([task, {}, task], tasks)

    def test_fetch_wraps_request_errors(self):
        for error in (requests.ConnectionError("offline"), requests.Timeout("timed out")):
            with self.subTest(error=type(error).__name__):
                session = Mock()
                session.get.side_effect = error

                with self.assertRaisesRegex(backfill_download_urls.task_api.TaskAPIError, "已完成任务查询失败"):
                    backfill_download_urls.fetch_completed_tasks(
                        base_url=API_BASE, key=API_KEY, timeout=30, session=session
                    )
                session.get.assert_called_once()

    def test_fetch_wraps_http_error(self):
        session = Mock()
        session.get.return_value.raise_for_status.side_effect = requests.HTTPError("unauthorized")

        with self.assertRaisesRegex(backfill_download_urls.task_api.TaskAPIError, "已完成任务查询失败"):
            backfill_download_urls.fetch_completed_tasks(
                base_url=API_BASE, key=API_KEY, timeout=30, session=session
            )
        session.get.return_value.json.assert_not_called()

    def test_fetch_wraps_invalid_json(self):
        session = Mock()
        session.get.return_value.json.side_effect = ValueError("invalid JSON")

        with self.assertRaisesRegex(backfill_download_urls.task_api.TaskAPIError, "已完成任务查询失败"):
            backfill_download_urls.fetch_completed_tasks(
                base_url=API_BASE, key=API_KEY, timeout=30, session=session
            )

    def test_fetch_rejects_invalid_payload(self):
        payloads = (
            None,
            [],
            "success",
            {"status": "error", "data": []},
            {"status": "success"},
            {"status": "success", "data": None},
            {"status": "success", "data": {}},
            {"status": "success", "data": ""},
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                session = Mock()
                session.get.return_value = self.response(payload)

                with self.assertRaisesRegex(backfill_download_urls.task_api.TaskAPIError, "已完成任务接口返回失败"):
                    backfill_download_urls.fetch_completed_tasks(
                        base_url=API_BASE, key=API_KEY, timeout=30, session=session
                    )

    def test_builds_html_and_pptx_download_urls_from_actual_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            ccn_root = Path(temporary)
            report = ccn_root / "type" / "project" / "report"
            report.mkdir(parents=True)
            (report / "source_understanding_review.html").write_text("report", encoding="utf-8")
            (report / "single_page_tech_report.pptx").write_bytes(b"pptx")
            task = {
                "task_id": "TASK-1",
                "latest_result": {
                    "artifact_urls": [
                        "https://github.com/MozhiJiawei/ccn-report/tree/main/type/project/report"
                    ]
                },
            }

            urls = backfill_download_urls.artifact_urls_for_task(
                task, ccn_root=ccn_root, config=CONFIG
            )

            self.assertEqual(
                [
                    "https://github.com/MozhiJiawei/ccn-report/tree/main/type/project/report",
                    "https://media.githubusercontent.com/media/MozhiJiawei/ccn-report/refs/heads/main/type/project/report/source_understanding_review.html?download=true",
                    "https://github.com/MozhiJiawei/ccn-report/raw/refs/heads/main/type/project/report/single_page_tech_report.pptx?download=1",
                ],
                urls,
            )

    def test_supports_legacy_html_only_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            ccn_root = Path(temporary)
            report = ccn_root / "type" / "project" / "legacy"
            report.mkdir(parents=True)
            (report / "source_understanding.html").write_text("legacy", encoding="utf-8")
            task = {
                "task_id": "TASK-OLD",
                "latest_result": {
                    "artifact_urls": [
                        "https://github.com/MozhiJiawei/ccn-report/tree/main/type/project/legacy"
                    ]
                },
            }

            urls = backfill_download_urls.artifact_urls_for_task(
                task, ccn_root=ccn_root, config=CONFIG
            )

            self.assertEqual(2, len(urls))
            self.assertTrue(urls[1].endswith("/source_understanding.html?download=true"))

    def test_does_not_guess_when_multiple_unrecognized_html_files_exist(self):
        with tempfile.TemporaryDirectory() as temporary:
            ccn_root = Path(temporary)
            report = ccn_root / "type" / "project" / "ambiguous"
            report.mkdir(parents=True)
            (report / "one.html").write_text("one", encoding="utf-8")
            (report / "two.html").write_text("two", encoding="utf-8")
            task = {
                "task_id": "TASK-AMBIGUOUS",
                "latest_result": {
                    "artifact_urls": [
                        "https://github.com/MozhiJiawei/ccn-report/tree/main/type/project/ambiguous"
                    ]
                },
            }

            self.assertIsNone(
                backfill_download_urls.artifact_urls_for_task(
                    task, ccn_root=ccn_root, config=CONFIG
                )
            )


if __name__ == "__main__":
    unittest.main()
