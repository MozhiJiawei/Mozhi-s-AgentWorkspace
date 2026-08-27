from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import unittest


LOOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOOP_ROOT))

import backfill_download_urls  # noqa: E402


CONFIG = {"ccn_report_repository_url": "https://github.com/MozhiJiawei/ccn-report"}


class BackfillDownloadUrlsTests(unittest.TestCase):
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
