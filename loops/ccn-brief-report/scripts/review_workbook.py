"""Collect local review evidence and read human decisions; never mutate reports/API."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_deliverables import load_tasks, validate_tasks  # noqa: E402

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def directory_contents(folder: Path) -> str:
    return '\n'.join(item.name + ('/' if item.is_dir() else '')
                     for item in sorted(folder.iterdir(), key=lambda item: (item.name.casefold(), item.name)))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def confined(directory: Path, work_root: Path) -> Path:
    directory = directory.resolve()
    if not directory.is_relative_to(work_root.resolve()):
        raise ValueError('审阅目录必须位于当前工作根目录内')
    return directory


def collect(tasks_path: Path, ccn_root: Path) -> dict:
    ccn_root = ccn_root.resolve()
    tasks = load_tasks(tasks_path)
    if not tasks:
        raise ValueError('没有任务，不生成空审阅表')
    registry_path = ccn_root / 'classification/categories.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    categories = {p for p in registry} | {f'{p}/{c}' for p, kids in registry.items() for c in kids}
    results = validate_tasks(tasks, ccn_root)
    rows, evidence = [], []
    for task, result in zip(tasks, results):
        if result.errors:
            raise ValueError(f'{result.task_id}: {"; ".join(result.errors)}')
        for key in ('task_id', 'content', 'url'):
            if not isinstance(task.get(key), str) or not task[key].strip():
                raise ValueError(f'任务缺少 {key}')
        if not isinstance(task.get('row_number'), int) or isinstance(task['row_number'], bool):
            raise ValueError('row_number 必须是整数')
        if not re.match(r'^https?://', task['url']):
            raise ValueError('任务信息源必须为 HTTP(S) URL')
        category = task.get('category')
        if category is not None and category not in categories:
            raise ValueError('API 指定分类未注册')
        folder = result.report_dir.resolve()
        actual = folder.parent.relative_to(ccn_root).as_posix()
        if actual not in categories:
            raise ValueError(f'未注册的归档分类：{actual}')
        rows.append([task['row_number'], task['task_id'], task['content'].splitlines()[0],
                     task['url'], category or '未指定（自动分类）', actual, folder.as_posix(),
                     directory_contents(folder)])
        for filename in (f'{result.basename}.html', f'{result.basename}.pptx', 'README.md'):
            file = folder / filename
            data = file.read_bytes()
            if not data or data.startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise ValueError(f'空文件或 LFS 占位文件：{file}')
            status = '存在且非空'
            if file.suffix == '.pptx':
                with ZipFile(file) as archive:
                    slides = [n for n in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)]
                    if archive.testzip() or len(slides) != 1:
                        raise ValueError(f'PPTX 结构异常或不是单页：{file}')
                    for name in slides:
                        ET.fromstring(archive.read(name))
                status = 'ZIP 完整；1 页（未验证视觉效果）'
            evidence.append({'task_id': task['task_id'], 'number': task['row_number'],
                             'name': filename, 'path': file.as_posix(), 'bytes': len(data),
                             'sha256': digest(file), 'status': status})
    return {'schema': 1, 'tasks': tasks, 'tasks_sha256': digest(tasks_path),
            'tasks_path': tasks_path.resolve().as_posix(), 'ccn_root': ccn_root.as_posix(),
            'registry_sha256': digest(registry_path), 'registry': registry,
            'rows': rows, 'evidence': evidence, 'approval_row': len(rows) + 10}


def prepare(args: argparse.Namespace) -> None:
    directory = confined(args.review_dir, args.work_root)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('审阅目录已有产物；使用新的 review-dir，禁止覆盖人工输入')
    payload = collect(args.tasks.resolve(), args.ccn_root)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / 'manifest.json', payload)


def finish(directory: Path) -> None:
    """Add native links/names: Artifact Tool lacks working hyperlink export here."""
    payload = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    links = json.loads((directory / 'links.json').read_text(encoding='utf-8'))
    book = directory / 'review.xlsx'
    with ZipFile(book) as archive:
        parts = {n: archive.read(n) for n in archive.namelist()}
    for index in (1,):
        sheet = ET.fromstring(parts[f'xl/worksheets/sheet{index}.xml'])
        old_links = sheet.find(f'{{{NS}}}hyperlinks')
        if old_links is not None:
            sheet.remove(old_links)
        links_node = ET.Element(f'{{{NS}}}hyperlinks')
        after = {'printOptions', 'pageMargins', 'pageSetup', 'headerFooter', 'drawing', 'tableParts', 'extLst'}
        position = next((i for i, x in enumerate(sheet) if x.tag.split('}')[-1] in after), len(sheet))
        sheet.insert(position, links_node)
        relationships = ET.Element(f'{{{PKG}}}Relationships')
        for i, link in enumerate((x for x in links if x['sheet'] == index), 1):
            rid = f'rIdReview{i}'
            ET.SubElement(links_node, f'{{{NS}}}hyperlink', {'ref': link['cell'], f'{{{REL}}}id': rid})
            ET.SubElement(relationships, f'{{{PKG}}}Relationship', {
                'Id': rid, 'Type': REL + '/hyperlink', 'Target': link['target'], 'TargetMode': 'External'})
        for item in sheet.findall(f'.//{{{NS}}}dataValidation'):
            item.set('allowBlank', '1')
            item.set('showErrorMessage', '1')
            item.set('errorStyle', 'stop')
            item.set('errorTitle', '请从下拉列表选择')
            item.set('error', '请选择合法值；更换一级后需重选二级。')
        parts[f'xl/worksheets/sheet{index}.xml'] = ET.tostring(sheet, encoding='utf-8', xml_declaration=True)
        parts[f'xl/worksheets/_rels/sheet{index}.xml.rels'] = ET.tostring(relationships, encoding='utf-8', xml_declaration=True)
    workbook = ET.fromstring(parts['xl/workbook.xml'])
    names = workbook.find(f'{{{NS}}}definedNames')
    if names is None:
        names = ET.Element(f'{{{NS}}}definedNames')
        calc = workbook.find(f'{{{NS}}}calcPr')
        workbook.insert(list(workbook).index(calc) if calc is not None else len(workbook), names)
    for item in list(names):
        if item.attrib.get('name', '').startswith('CCN_'):
            names.remove(item)
    def name(key: str, value: str) -> None:
        ET.SubElement(names, f'{{{NS}}}definedName', {'name': key}).text = value
    name('CCN_PRIMARY', f"'分类枚举'!$E$5:$E${4 + len(payload['registry'])}")
    name('CCN_EMPTY', "'分类枚举'!$D$5")
    for i, (primary, children) in enumerate(payload['registry'].items()):
        col = column_name(i + 6)
        name(f'CCN_SUB_{primary[:2]}', f"'分类枚举'!${col}$5:${col}${4 + len(children)}")
    parts['xl/workbook.xml'] = ET.tostring(workbook, encoding='utf-8', xml_declaration=True)
    temporary = book.with_suffix('.staging')
    with ZipFile(temporary, 'w', ZIP_DEFLATED) as archive:
        for key, value in parts.items():
            archive.writestr(key, value)
    temporary.replace(book)
    with ZipFile(book) as archive:
        if archive.testzip():
            raise ValueError('Excel 导出包损坏')
        for i in range(1, 3):
            sheet = ET.fromstring(archive.read(f'xl/worksheets/sheet{i}.xml'))
            if sheet.findall(f'.//{{{NS}}}c[@t="e"]'):
                raise ValueError('Excel 含错误单元格')


def column_name(index: int) -> str:
    text = ''
    while index:
        index, digit = divmod(index - 1, 26)
        text = chr(65 + digit) + text
    return text


def cells(archive: ZipFile, sheet_index: int) -> dict[str, str | int | float]:
    strings = []
    if 'xl/sharedStrings.xml' in archive.namelist():
        for node in ET.fromstring(archive.read('xl/sharedStrings.xml')):
            strings.append(''.join(node.itertext()))
    result = {}
    for node in ET.fromstring(archive.read(f'xl/worksheets/sheet{sheet_index}.xml')).findall(f'.//{{{NS}}}c'):
        kind = node.get('t')
        value = node.findtext(f'{{{NS}}}v', '')
        if kind == 's':
            value = strings[int(value)]
        elif kind == 'inlineStr':
            value = ''.join(node.find(f'{{{NS}}}is').itertext())
        elif kind not in ('str', 'e') and value:
            value = float(value)
        result[node.attrib['r']] = value
    return result


def read_decisions(directory: Path, workbook_path: Path) -> dict:
    manifest_path = directory / 'manifest.json'
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    if digest(Path(payload['tasks_path'])) != payload['tasks_sha256']:
        raise ValueError('任务快照已变化，必须重新生成审阅表')
    registry_path = Path(payload['ccn_root']) / 'classification/categories.json'
    if digest(registry_path) != payload['registry_sha256']:
        raise ValueError('分类枚举已变化，必须重新审阅')
    for item in payload['evidence']:
        file = Path(item['path'])
        if not file.is_file() or digest(file) != item['sha256']:
            raise ValueError(f'交付件已变化，必须重新审阅：{file}')
    with ZipFile(workbook_path) as archive:
        main, choices = cells(archive, 1), cells(archive, 2)
    if choices.get('I2') != digest(manifest_path):
        raise ValueError('审阅表不属于该批次快照')
    row = payload['approval_row']
    if main.get(f'B{row}') != '通过':
        raise ValueError('人类尚未明确批准：批次结论必须为“通过”')
    if not str(main.get(f'B{row+1}', '')).strip() or not str(main.get(f'B{row+2}', '')).strip():
        raise ValueError('请填写审核人和审核日期')
    decisions = []
    expected_ids = {r[1] for r in payload['rows']}
    present_ids = {v for k, v in main.items() if re.fullmatch(r'B\d+', k) and v in expected_ids}
    if present_ids != expected_ids:
        raise ValueError('审阅表任务覆盖不完整')
    for i, original in enumerate(payload['rows'], 8):
        for col, value in zip('ABCDEFGH', original):
            if main.get(f'{col}{i}', '') != value:
                raise ValueError(f'原始字段被改动或行被重排：{col}{i}')
        if directory_contents(Path(original[6])) != original[7]:
            raise ValueError('目录内容已变化，必须重新审阅')
        primary, secondary = (str(main.get(f'{col}{i}', '')).strip() for col in 'IJ')
        if not primary and secondary:
            raise ValueError('二级分类存在但未选一级')
        if primary and (primary not in payload['registry'] or
                        (secondary and secondary not in payload['registry'][primary])):
            raise ValueError('一级二级不匹配或枚举非法')
        selected = (primary + ('/' + secondary if secondary else '')) if primary else original[5]
        constraint = payload['tasks'][i-8].get('category')
        if constraint and selected != constraint and not ('/' not in constraint and selected.startswith(constraint + '/')):
            raise ValueError('人工修改与 API 指定分类冲突；不得自动覆盖服务端约束')
        decisions.append({'task_id': original[1], 'current_category': original[5],
                          'selected_category': selected, 'needs_move': selected != original[5],
                          'primary_only': '/' not in selected})
    return {'manifest_sha256': digest(manifest_path), 'workbook_sha256': digest(workbook_path),
            'reviewer': main[f'B{row+1}'], 'review_date': main[f'B{row+2}'],
            'status': 'classification_changes_requested' if any(x['needs_move'] for x in decisions) else 'approved',
            'decisions': decisions}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'finish', 'read'])
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--review-dir', type=Path, required=True)
    parser.add_argument('--tasks', type=Path)
    parser.add_argument('--ccn-root', type=Path)
    parser.add_argument('--workbook', type=Path)
    args = parser.parse_args()
    try:
        directory = confined(args.review_dir, args.work_root)
        if args.command == 'prepare':
            if args.tasks is None or args.ccn_root is None:
                raise ValueError('prepare 需要 --tasks 和 --ccn-root')
            prepare(args)
        elif args.command == 'finish':
            finish(directory)
        else:
            # A failed fresh read must not leave an older approval usable.
            (directory / 'decisions.json').unlink(missing_ok=True)
            decisions = read_decisions(directory, args.workbook or directory / 'review.xlsx')
            write_json(directory / 'decisions.json', decisions)
            print(decisions['status'])
        return 0
    except (ValueError, OSError, KeyError, BadZipFile, ET.ParseError) as exc:
        print(f'[error] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
