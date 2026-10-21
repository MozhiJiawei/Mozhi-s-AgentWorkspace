from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import review_workbook as review  # noqa: E402

PRIMARY = '02-智能体平台、协议与执行系统'
CHILD = 'Agent架构与编排'
OTHER = '03-AI推理与服务加速'


class ReviewWorkbookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ccn = self.root / 'ccn'
        registry = self.ccn / 'classification/categories.json'
        registry.parent.mkdir(parents=True)
        review.write_json(registry, {PRIMARY: [CHILD], OTHER: ['模型计算']})
        self.folder = self.ccn / PRIMARY / CHILD / '20260928-example-codex'
        self.folder.mkdir(parents=True)
        self.report = self.folder / 'Example.html'
        self.report.write_text('<html>actual report</html>', encoding='utf-8')
        with ZipFile(self.folder / 'Example.pptx', 'w') as archive:
            archive.writestr('ppt/slides/slide1.xml', '<slide/>')
        (self.folder / 'README.md').write_text(
            f'- 任务编号：TASK-1\n- 实际归档分类：{PRIMARY}/{CHILD}\n'
            '- [Example.html](./Example.html)\n- [Example.pptx](./Example.pptx)\n', encoding='utf-8')
        self.tasks = self.root / 'tasks.json'
        review.write_json(self.tasks, [{'row_number': 167, 'task_id': 'TASK-1',
                                      'content': '原始主题\n详细正文', 'url': 'https://example.com/source', 'category': None}])
        self.directory = self.root / 'review'
        self.directory.mkdir()

    def snapshot(self):
        payload = review.collect(self.tasks, self.ccn)
        review.write_json(self.directory / 'manifest.json', payload)
        return payload

    def workbook(self, payload, conclusion='通过', overrides=None, alter_source=False):
        values = {f'{col}8': value for col, value in zip('ABCDEFGH', payload['rows'][0])}
        values.update({f'B{payload["approval_row"]}': conclusion,
                       f'B{payload["approval_row"]+1}': 'Human', f'B{payload["approval_row"]+2}': '2026-10-09'})
        if overrides:
            values.update(dict(zip(('I8', 'J8'), overrides)))
        if alter_source:
            values['D8'] = 'https://wrong.example/'
        def xml(cells):
            sheet = ET.Element(f'{{{review.NS}}}worksheet')
            data = ET.SubElement(sheet, f'{{{review.NS}}}sheetData')
            for address, value in cells.items():
                node = ET.SubElement(data, f'{{{review.NS}}}c', {'r': address, 't': 'inlineStr'})
                ET.SubElement(ET.SubElement(node, f'{{{review.NS}}}is'), f'{{{review.NS}}}t').text = str(value)
            return ET.tostring(sheet)
        # Numeric API identifiers are genuinely numeric cells in exported Excel.
        first = ET.fromstring(xml(values))
        cell = first.find(f'.//{{{review.NS}}}c[@r="A8"]')
        cell.clear(); cell.set('r', 'A8'); ET.SubElement(cell, f'{{{review.NS}}}v').text = '167'
        book = self.directory / 'review.xlsx'
        with ZipFile(book, 'w') as archive:
            archive.writestr('xl/worksheets/sheet1.xml', ET.tostring(first))
            archive.writestr('xl/worksheets/sheet2.xml', xml({'I2': review.digest(self.directory / 'manifest.json')}))
        return book

    def test_maps_old_directory_by_task_id_and_preserves_raw_source(self):
        payload = self.snapshot()
        self.assertEqual(1, len(payload['rows']))
        self.assertIn('20260928-', payload['rows'][0][6])
        self.assertEqual('https://example.com/source', payload['rows'][0][3])
        self.assertEqual(3, len(payload['evidence']))

    def test_directory_contents_lists_actual_files_and_subdirectories(self):
        (self.folder / 'assets').mkdir()
        (self.folder / 'assets' / 'image.png').write_bytes(b'image')
        payload = self.snapshot()
        self.assertEqual('assets/\nExample.html\nExample.pptx\nREADME.md', payload['rows'][0][7])

    def test_pending_is_not_approval(self):
        payload = self.snapshot()
        with self.assertRaisesRegex(ValueError, '尚未明确批准'):
            review.read_decisions(self.directory, self.workbook(payload, '待审核'))

    def test_category_comes_from_directory_without_readme_declaration(self):
        readme = self.folder / 'README.md'
        readme.write_text(readme.read_text(encoding='utf-8').replace(
            f'- 实际归档分类：{PRIMARY}/{CHILD}\n', ''), encoding='utf-8')
        self.assertEqual(f'{PRIMARY}/{CHILD}', self.snapshot()['rows'][0][5])

    def test_readme_declaration_cannot_override_directory_category(self):
        readme = self.folder / 'README.md'
        readme.write_text(readme.read_text(encoding='utf-8').replace(
            f'- 实际归档分类：{PRIMARY}/{CHILD}', f'- 实际归档分类：{OTHER}/模型计算'), encoding='utf-8')
        self.assertEqual(f'{PRIMARY}/{CHILD}', self.snapshot()['rows'][0][5])

    def test_explicit_approval_without_changes(self):
        payload = self.snapshot()
        result = review.read_decisions(self.directory, self.workbook(payload))
        self.assertEqual('approved', result['status'])

    def test_valid_change_is_plan_not_final_approval(self):
        payload = self.snapshot()
        result = review.read_decisions(self.directory, self.workbook(payload, overrides=(OTHER, '模型计算')))
        self.assertEqual('classification_changes_requested', result['status'])

    def test_mismatched_secondary_is_rejected_even_if_excel_cache_looks_valid(self):
        payload = self.snapshot()
        with self.assertRaisesRegex(ValueError, '不匹配'):
            review.read_decisions(self.directory, self.workbook(payload, overrides=(OTHER, CHILD)))

    def test_modified_deliverable_invalidates_approval(self):
        payload = self.snapshot()
        book = self.workbook(payload)
        self.report.write_text('<html>changed</html>', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '交付件已变化'):
            review.read_decisions(self.directory, book)

    def test_modified_raw_field_is_rejected(self):
        payload = self.snapshot()
        with self.assertRaisesRegex(ValueError, '原始字段'):
            review.read_decisions(self.directory, self.workbook(payload, alter_source=True))

    def test_api_constraint_cannot_be_overridden(self):
        tasks = json.loads(self.tasks.read_text(encoding='utf-8'))
        tasks[0]['category'] = PRIMARY
        review.write_json(self.tasks, tasks)
        payload = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'API 指定分类冲突'):
            review.read_decisions(self.directory, self.workbook(payload, overrides=(OTHER, '模型计算')))

    def test_lfs_pointer_rejected(self):
        self.report.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:abc\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'LFS'):
            self.snapshot()

    def test_review_cannot_escape_work_root(self):
        with self.assertRaisesRegex(ValueError, '工作根目录'):
            review.confined(self.root.parent, self.root)


if __name__ == '__main__':
    unittest.main()
