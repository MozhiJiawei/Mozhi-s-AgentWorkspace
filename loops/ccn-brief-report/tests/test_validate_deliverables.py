from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


LOOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOOP_ROOT))

import validate_deliverables as validator  # noqa: E402


class ValidateDeliverablesTests(unittest.TestCase):
    def make_report(
        self,
        root: Path,
        task_id: str,
        basename: str = "RAC-参考感知激活压缩",
        *,
        html_basename: str | None = None,
        pptx_basename: str | None = None,
        readme_links: bool = True,
        include_html: bool = True,
        include_pptx: bool = True,
    ) -> Path:
        report = root / task_id.lower()
        report.mkdir(parents=True)
        html_name = f"{html_basename or basename}.html"
        pptx_name = f"{pptx_basename or basename}.pptx"
        if include_html:
            (report / html_name).write_text("html", encoding="utf-8")
        if include_pptx:
            (report / pptx_name).write_bytes(b"pptx")
        links = (
            f"- [{html_name}](./{html_name})\n- [{pptx_name}](./{pptx_name})\n"
            if readme_links
            else "- [wrong.html](./wrong.html)\n"
        )
        (report / "README.md").write_text(
            f"# Report\n\n- 任务编号：`{task_id}`\n\n## 交付件说明\n\n{links}",
            encoding="utf-8",
        )
        return report

    def validate_one(self, root: Path, task_id: str = "TASK-1"):
        return validator.validate_tasks([{"task_id": task_id}], root)[0]

    def test_valid_human_readable_basename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_report(root, "TASK-1")
            result = self.validate_one(root)
            self.assertEqual([], result.errors)
            self.assertEqual("RAC-参考感知激活压缩", result.basename)

    def test_rejects_generic_basename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_report(root, "TASK-1", "source_understanding_review")
            self.assertTrue(any("通用名称" in error for error in self.validate_one(root).errors))

    def test_rejects_mismatched_basenames(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_report(root, "TASK-1", html_basename="Alpha-方法", pptx_basename="Beta-方法")
            self.assertTrue(any("不一致" in error for error in self.validate_one(root).errors))

    def test_rejects_illegal_whitespace_and_overlong_names(self):
        invalid_names = ("Alpha 报告", "Alpha:报告", "A" * 61)
        for name in invalid_names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_report(root, "TASK-1", name)
                self.assertNotEqual([], self.validate_one(root).errors)

    def test_rejects_current_batch_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_report(root, "TASK-1", "Alpha-方法")
            self.make_report(root, "TASK-2", "Alpha-方法")
            results = validator.validate_tasks(
                [{"task_id": "TASK-1"}, {"task_id": "TASK-2"}], root
            )
            self.assertTrue(all(any("当前批次内重复" in error for error in item.errors) for item in results))

    def test_rejects_historical_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_report(root, "OLD-1", "Alpha-方法")
            self.make_report(root, "TASK-1", "Alpha-方法")
            result = self.validate_one(root)
            self.assertTrue(any("历史" in error for error in result.errors))

    def test_rejects_readme_link_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_report(root, "TASK-1", readme_links=False)
            self.assertTrue(any("README 交付件链接" in error for error in self.validate_one(root).errors))

    def test_rejects_missing_deliverable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_report(root, "TASK-1", include_pptx=False)
            self.assertTrue(any("PPTX" in error for error in self.validate_one(root).errors))

    def test_cli_loads_work_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = root / "pending.json"
            tasks.write_text(json.dumps([{"task_id": "TASK-1"}]), encoding="utf-8")
            self.assertEqual([{"task_id": "TASK-1"}], validator.load_tasks(tasks))


if __name__ == "__main__":
    unittest.main()
