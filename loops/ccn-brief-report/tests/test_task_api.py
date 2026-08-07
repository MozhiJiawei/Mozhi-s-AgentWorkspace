from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests


LOOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOOP_ROOT))

import task_api  # noqa: E402


API_BASE = "https://ccn-api.example.test"
API_KEY = "test-api-key-" + "x" * 32


class TaskAPITests(unittest.TestCase):
    def response(self, payload, status_code=200):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        response.status_code = status_code
        return response

    def test_fetch_empty_tasks(self):
        session = Mock()
        session.get.return_value = self.response({"status": "success", "data": []})

        tasks = task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

        self.assertEqual([], tasks)
        session.get.assert_called_once_with(
            f"{API_BASE}/api/v1/tasks",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"status": "pending", "limit": 500},
            timeout=(5, 30),
        )

    def test_fetch_normalizes_and_sorts_tasks(self):
        session = Mock()
        session.get.return_value = self.response(
            {
                "status": "success",
                "data": [
                    {
                        "row_number": "3",
                        "task_id": "TASK-2",
                        "content": "two",
                        "url": "https://example.test/2",
                        "hotspot_id": "HS-2",
                        "period": "2026-W32",
                        "status": "未领取",
                    },
                    {
                        "row_number": 2,
                        "task_id": "TASK-1",
                        "content": "one",
                        "url": "https://example.test/1",
                        "hotspot_id": "HS-1",
                        "period": "2026-W32",
                    },
                ],
            }
        )

        tasks = task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

        self.assertEqual(["TASK-1", "TASK-2"], [task["task_id"] for task in tasks])
        self.assertEqual(3, tasks[1]["row_number"])
        self.assertEqual("", tasks[0]["status"])

    def test_fetch_rejects_missing_fields(self):
        session = Mock()
        session.get.return_value = self.response(
            {"status": "success", "data": [{"row_number": 2, "task_id": "TASK-1"}]}
        )

        with self.assertRaises(task_api.TaskAPIError):
            task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

    def test_fetch_rejects_api_failure(self):
        session = Mock()
        session.get.return_value = self.response({"status": "error", "message": "bad"})

        with self.assertRaises(task_api.TaskAPIError):
            task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

    def test_fetch_rejects_duplicate_task_ids_with_different_row_numbers(self):
        session = Mock()
        duplicate = {
            "task_id": "TASK-1",
            "content": "one",
            "url": "https://example.test/1",
            "hotspot_id": "HS-1",
            "period": "2026-W32",
        }
        session.get.return_value = self.response(
            {
                "status": "success",
                "data": [
                    {"row_number": 3, **duplicate},
                    {"row_number": 2, **duplicate},
                ],
            }
        )

        with self.assertRaisesRegex(task_api.TaskAPIError, "内容冲突"):
            task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

    def test_fetch_rejects_conflicting_duplicate_task_ids(self):
        session = Mock()
        session.get.return_value = self.response(
            {
                "status": "success",
                "data": [
                    {
                        "row_number": 2,
                        "task_id": "TASK-1",
                        "content": "one",
                        "url": "https://example.test/1",
                        "hotspot_id": "HS-1",
                        "period": "2026-W32",
                    },
                    {
                        "row_number": 3,
                        "task_id": "TASK-1",
                        "content": "different",
                        "url": "https://example.test/1",
                        "hotspot_id": "HS-1",
                        "period": "2026-W32",
                    },
                ],
            }
        )

        with self.assertRaisesRegex(task_api.TaskAPIError, "内容冲突"):
            task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

    def test_fetch_rejects_unsafe_task_id_and_source_url(self):
        base = {
            "row_number": 2,
            "content": "one",
            "hotspot_id": "HS-1",
            "period": "2026-W32",
        }
        for task_id, source_url in (
            ("../escape", "https://example.test/1"),
            (".hidden", "https://example.test/1"),
            ("-task", "https://example.test/1"),
            ("TASK-1", "file:///secret"),
            ("TASK-1", "http://example.test/1"),
        ):
            with self.subTest(task_id=task_id, source_url=source_url):
                session = Mock()
                session.get.return_value = self.response(
                    {
                        "status": "success",
                        "data": [{**base, "task_id": task_id, "url": source_url}],
                    }
                )

                with self.assertRaises(task_api.TaskAPIError):
                    task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

    def test_fetch_follows_api_pagination(self):
        session = Mock()
        session.get.side_effect = [
            self.response(
                {
                    "status": "success",
                    "data": [
                        {
                            "row_number": 1,
                            "task_id": "TASK-1",
                            "content": "one",
                            "url": "https://example.test/1",
                            "hotspot_id": "HS-1",
                            "period": "2026-W32",
                        }
                    ],
                    "pagination": {"has_more": True, "next_cursor": 1},
                }
            ),
            self.response(
                {
                    "status": "success",
                    "data": [
                        {
                            "row_number": 2,
                            "task_id": "TASK-2",
                            "content": "two",
                            "url": "https://example.test/2",
                            "hotspot_id": "HS-2",
                            "period": "2026-W32",
                        }
                    ],
                    "pagination": {"has_more": False, "next_cursor": None},
                }
            ),
        ]

        tasks = task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

        self.assertEqual(["TASK-1", "TASK-2"], [task["task_id"] for task in tasks])
        self.assertEqual(1, session.get.call_args_list[1].kwargs["params"]["cursor"])

    def test_fetch_rejects_repeated_pagination_cursor(self):
        session = Mock()
        page = {"status": "success", "data": [], "pagination": {"has_more": True, "next_cursor": 1}}
        session.get.side_effect = [self.response(page), self.response(page)]

        with self.assertRaisesRegex(task_api.TaskAPIError, "没有前进"):
            task_api.fetch_tasks(base_url=API_BASE, key=API_KEY, timeout=30, session=session)

    def test_api_key_comes_from_environment_or_private_config(self):
        with patch.dict(os.environ, {"CCN_API_KEY": ""}):
            self.assertEqual(API_KEY, task_api.api_key({"api_key": API_KEY}))
        with patch.dict(os.environ, {"CCN_API_KEY": API_KEY}):
            self.assertEqual(API_KEY, task_api.api_key({"api_key": "ignored"}))

    def test_api_key_is_required(self):
        with patch.dict(os.environ, {"CCN_API_KEY": ""}):
            with self.assertRaisesRegex(task_api.TaskAPIError, "缺少 CCN API Key"):
                task_api.api_key({})

    def test_write_json_uses_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "tasks.json"
            task_api.write_json(output, [{"content": "中文"}])

            self.assertEqual([{"content": "中文"}], json.loads(output.read_text(encoding="utf-8")))

    def test_fetch_can_isolate_invalid_task_without_blocking_valid_tasks(self):
        session = Mock()
        session.get.return_value = self.response(
            {
                "status": "success",
                "data": [
                    {"row_number": 1, "task_id": "BROKEN"},
                    {
                        "row_number": 2,
                        "task_id": "TASK-2",
                        "content": "valid",
                        "url": "https://example.test/2",
                        "hotspot_id": "HS-2",
                        "period": "2026-W32",
                    },
                ],
            }
        )
        rejected = []

        tasks = task_api.fetch_tasks(
            base_url=API_BASE,
            key=API_KEY,
            timeout=30,
            session=session,
            rejected=rejected,
        )

        self.assertEqual(["TASK-2"], [task["task_id"] for task in tasks])
        self.assertEqual("BROKEN", rejected[0]["task_id"])

    def test_complete_result_uses_stable_idempotency_and_confirms_remote_state(self):
        session = Mock()
        session.post.return_value = self.response({"status": "success", "data": {}})
        artifact_url = "https://github.com/MozhiJiawei/ccn-report/tree/main/type/project/report"
        session.get.return_value = self.response(
            {
                "status": "success",
                "data": {
                    "task_id": "TASK-1",
                    "status": "completed",
                    "latest_result": {"outcome": "completed", "artifact_urls": [artifact_url]},
                },
            }
        )

        task = task_api.submit_result(
            base_url=API_BASE,
            key=API_KEY,
            task_id="TASK-1",
            artifact_url=artifact_url,
            timeout=30,
            session=session,
        )

        self.assertEqual("completed", task["status"])
        idempotency_key = session.post.call_args.kwargs["headers"]["Idempotency-Key"]
        self.assertTrue(idempotency_key.startswith("ccn-report-TASK-1-"))

    def test_complete_recovers_when_post_response_is_lost_but_remote_state_matches(self):
        session = Mock()
        session.post.side_effect = requests.ConnectionError("response lost")
        artifact_url = "https://github.com/MozhiJiawei/ccn-report/tree/main/type/project/report"
        session.get.return_value = self.response(
            {
                "status": "success",
                "data": {
                    "task_id": "TASK-1",
                    "status": "completed",
                    "latest_result": {"outcome": "completed", "artifact_urls": [artifact_url]},
                },
            }
        )

        task = task_api.submit_result(
            base_url=API_BASE,
            key=API_KEY,
            task_id="TASK-1",
            artifact_url=artifact_url,
            timeout=30,
            session=session,
        )

        self.assertEqual("completed", task["status"])

    def test_artifact_url_must_target_configured_main_report_directory(self):
        config = {"ccn_report_repository_url": "https://github.com/MozhiJiawei/ccn-report"}
        valid = "https://github.com/MozhiJiawei/ccn-report/tree/main/type/project/report"
        self.assertEqual(valid, task_api.validate_artifact_url(valid, config))
        encoded = (
            "https://github.com/MozhiJiawei/ccn-report/tree/main/"
            "%E5%AD%A6%E6%9C%AF%E8%AE%BA%E6%96%87%E5%88%86%E6%9E%90/Agent/report"
        )
        unicode_url = "https://github.com/MozhiJiawei/ccn-report/tree/main/学术论文分析/Agent/report"
        self.assertEqual(unicode_url, task_api.validate_artifact_url(encoded, config))
        reserved = "https://github.com/MozhiJiawei/ccn-report/tree/main/type/report%20name%2Fpart"
        self.assertEqual(reserved, task_api.validate_artifact_url(reserved, config))
        for invalid in (
            "https://example.com/report",
            "https://github.com/MozhiJiawei/ccn-report",
            "https://github.com/MozhiJiawei/ccn-report/tree/dev/report",
            "https://github.com/MozhiJiawei/ccn-report/tree/main/report?download=1",
            "https://github.com/MozhiJiawei/ccn-report/tree/main/type/../report",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(task_api.TaskAPIError):
                    task_api.validate_artifact_url(invalid, config)


if __name__ == "__main__":
    unittest.main()
