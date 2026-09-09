import sys
import unittest
import tempfile
from contextlib import ExitStack
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import task_api
from task_service.app.domain.categories import category_path_error
from validate_deliverables import validate_category_constraint, DeliverableValidationError


class CategoriesTests(unittest.TestCase):
    def test_complete_reads_authoritative_category_and_blocks_wrong_path(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            report = root / '04-AI模型' / 'report'
            report.mkdir(parents=True)
            (report / 'Example.html').write_text('html')
            (report / 'Example.pptx').write_bytes(b'pptx')
            for name, value in {
                'load_config': {'ccn_report_repository_url': 'https://example.test'},
                'load_credentials': {}, 'api_base': 'https://example.test',
                'api_key': 'test-key', 'validate_completion_report': 'Example',
            }.items():
                stack.enter_context(patch.object(task_api, name, return_value=value))
            for name in ['validate_artifact_url', 'validate_download_url']:
                stack.enter_context(patch.object(task_api, name, side_effect=lambda value, *a, **kw: value))
            stack.enter_context(patch.object(task_api, 'DEFAULT_CCN_ROOT', root))
            fetch = stack.enter_context(patch.object(task_api, 'fetch_task'))
            submit = stack.enter_context(patch.object(task_api, 'submit_result'))
            args = task_api.build_parser().parse_args([
                '--work-root', str(root), 'complete', '--task-id', 'TASK-1',
                '--report-path', str(report),
                '--artifact-url', 'https://example.test/tree/main/04-AI模型/report',
                '--html-download-url', 'https://example.test/Example.html',
                '--pptx-download-url', 'https://example.test/Example.pptx',
            ])
            for selected in ['01-AI应用与产品化场景', '04-AI模型/多模态模型与模型架构', 'invalid']:
                fetch.return_value = {'category': selected}
                with self.subTest(category=selected), self.assertRaises(task_api.TaskAPIError):
                    args.func(args)
            fetch.return_value = {'category': '04-AI模型'}
            args.artifact_url = 'https://example.test/tree/main/04-AI模型/different-report'
            with self.assertRaises(task_api.TaskAPIError):
                args.func(args)
            self.assertEqual(fetch.call_count, 4)
            submit.assert_not_called()
            self.assertFalse((root / 'loop-ccn-brief-report' / 'state.json').exists())

    def test_normalization_keeps_or_rejects_category(self):
        task = dict(row_number=1, task_id='TEST-1', content='content', url='https://example.com', hotspot_id='H1',period='P1')
        self.assertIsNone(task_api.normalize_task(task,1)['category'])
        self.assertEqual(task_api.normalize_task({**task,'category':'04-AI模型'},1)['category'],'04-AI模型')
        for invalid in ['', 'AI模型', 4]:
            with self.assertRaises(task_api.TaskAPIError): task_api.normalize_task({**task,'category':invalid},1)
        with self.assertRaises(task_api.TaskAPIError):
            task_api.deduplicate_tasks([task,{**task,'category':'04-AI模型'}])

    def test_parent_constraints(self):
        self.assertIsNone(category_path_error('04-AI模型', '04-AI模型'))
        self.assertIsNone(category_path_error('04-AI模型/多模态模型与模型架构', '04-AI模型'))
        self.assertIsNotNone(category_path_error('04-AI模型','04-AI模型/多模态模型与模型架构'))
        self.assertIsNotNone(category_path_error('01-AI应用与产品化场景','04-AI模型'))
        self.assertIsNotNone(category_path_error('04-AI模型/多模态模型与模型架构/厂商','04-AI模型'))
        self.assertIsNone(category_path_error('anywhere',None))
        with self.assertRaises(DeliverableValidationError):
            validate_category_constraint(Path.cwd().parent,Path.cwd(),'04-AI模型')
