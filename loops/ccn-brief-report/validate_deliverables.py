from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterable
from task_service.app.domain.categories import category_path_error


GENERIC_BASENAMES = {
    "report",
    "presentation",
    "slides",
    "source-understanding-review",
    "source_understanding_review",
    "single-page-tech-report",
    "single_page_tech_report",
    "tech-report",
    "tech_report",
}
WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
ILLEGAL_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
DATE_TOKEN = re.compile(r"(?:19|20)\d{2}(?:[-_.]?\d{2}){1,2}")
README_TASK_ID = re.compile(r"(?m)^\s*-?\s*任务编号[：:]\s*`?([^`\s]+)`?\s*$")
DELIVERABLE_LINK = re.compile(r"\[([^\]\r\n]+)\]\(\./(.+?\.(?:html|pptx))\)", re.IGNORECASE)


class DeliverableValidationError(RuntimeError):
    pass


@dataclass
class TaskValidation:
    task_id: str
    report_dir: Path | None = None
    basename: str | None = None
    errors: list[str] = field(default_factory=list)


def load_tasks(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise DeliverableValidationError("工作队列顶层必须是数组")
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("task_id"), str):
            raise DeliverableValidationError(f"工作队列第 {index} 条缺少字符串 task_id")
        task_id = item["task_id"]
        if task_id in seen:
            raise DeliverableValidationError(f"工作队列包含重复任务编号：{task_id}")
        seen.add(task_id)
        tasks.append(item)
    return tasks


def readme_task_ids(readme: Path) -> list[str]:
    return README_TASK_ID.findall(readme.read_text(encoding="utf-8"))


def walk_files(root: Path) -> Iterable[Path]:
    for parent, _directories, filenames in os.walk(root):
        for filename in filenames:
            yield Path(parent) / filename


def map_task_directories(ccn_root: Path, task_ids: Iterable[str]) -> dict[str, list[Path]]:
    wanted = set(task_ids)
    matches = {task_id: [] for task_id in wanted}
    if not ccn_root.is_dir():
        raise DeliverableValidationError(f"CCN 归档根目录不存在：{ccn_root}")
    for readme in walk_files(ccn_root):
        if readme.name != "README.md":
            continue
        for task_id in readme_task_ids(readme):
            if task_id in wanted:
                matches[task_id].append(readme.parent)
    return matches


def normalized_generic_name(basename: str) -> str:
    return re.sub(r"[-_\s]+", "-", basename.casefold()).strip("-")


def basename_errors(basename: str, task_id: str) -> list[str]:
    errors: list[str] = []
    length = len(basename)
    if not 2 <= length <= 60:
        errors.append(f"主题短名长度必须为 2–60 个字符，当前为 {length}")
    if any(character.isspace() for character in basename):
        errors.append("主题短名不得包含空白字符")
    if ILLEGAL_WINDOWS_CHARS.search(basename):
        errors.append("主题短名包含 Windows 非法字符")
    if basename.endswith((".", " ")):
        errors.append("主题短名不得以句点或空格结尾")
    if basename.casefold() in WINDOWS_RESERVED_NAMES:
        errors.append("主题短名不得使用 Windows 保留名称")
    if normalized_generic_name(basename) in {
        normalized_generic_name(name) for name in GENERIC_BASENAMES
    }:
        errors.append("主题短名是无区分度的通用名称")
    if task_id.casefold() in basename.casefold():
        errors.append("主题短名不得包含任务编号")
    if DATE_TOKEN.search(basename):
        errors.append("主题短名不得包含批次日期")
    return errors


def deliverable_files(report_dir: Path, suffix: str) -> list[Path]:
    return sorted(
        (path for path in report_dir.iterdir() if path.is_file() and path.suffix.casefold() == suffix),
        key=lambda path: path.name.casefold(),
    )


def validate_readme_links(readme: Path, html_name: str, pptx_name: str) -> list[str]:
    delivery_links = DELIVERABLE_LINK.findall(readme.read_text(encoding="utf-8"))
    expected = {(html_name, html_name), (pptx_name, pptx_name)}
    if set(delivery_links) != expected or len(delivery_links) != 2:
        return [
            "README 交付件链接必须且只能精确指向 "
            f"./{html_name} 与 ./{pptx_name}，且链接文字使用实际文件名"
        ]
    return []


def validate_report_directory(
    report_dir: Path,
    task_id: str,
    *,
    historical_basenames: set[str] | None = None,
) -> TaskValidation:
    result = TaskValidation(task_id=task_id, report_dir=report_dir)
    readmes = deliverable_files(report_dir, ".md")
    readmes = [path for path in readmes if path.name.casefold() == "readme.md"]
    html_files = deliverable_files(report_dir, ".html")
    pptx_files = deliverable_files(report_dir, ".pptx")
    if len(readmes) != 1:
        result.errors.append(f"要求恰有一个 README.md，实际为 {len(readmes)}")
    if len(html_files) != 1:
        result.errors.append(f"要求恰有一个 HTML，实际为 {len(html_files)}")
    if len(pptx_files) != 1:
        result.errors.append(f"要求恰有一个 PPTX，实际为 {len(pptx_files)}")
    if len(html_files) != 1 or len(pptx_files) != 1:
        return result

    html_file = html_files[0]
    pptx_file = pptx_files[0]
    if html_file.suffix != ".html" or pptx_file.suffix != ".pptx":
        result.errors.append("交付件扩展名必须精确使用小写 .html 与 .pptx")
    if html_file.stem != pptx_file.stem:
        result.errors.append(
            f"HTML/PPTX basename 不一致：{html_file.stem!r} != {pptx_file.stem!r}"
        )
        return result

    result.basename = html_file.stem
    result.errors.extend(basename_errors(result.basename, task_id))
    if historical_basenames and result.basename.casefold() in historical_basenames:
        result.errors.append("主题短名与历史 CCN 交付件重名")
    if len(readmes) == 1:
        ids = readme_task_ids(readmes[0])
        if ids != [task_id]:
            result.errors.append(
                f"README 必须包含且只包含精确任务编号 {task_id}，实际为 {ids or '未找到'}"
            )
        result.errors.extend(validate_readme_links(readmes[0], html_file.name, pptx_file.name))
    return result


def historical_basenames(ccn_root: Path, current_dirs: set[Path]) -> set[str]:
    names: set[str] = set()
    resolved_current = {path.resolve() for path in current_dirs}
    for path in walk_files(ccn_root):
        if (
            path.suffix.casefold() in {".html", ".pptx"}
            and path.parent.resolve() not in resolved_current
        ):
            names.add(path.stem.casefold())
    return names


def validate_category_constraint(report_dir: Path, ccn_root: Path, category: object) -> None:
    try:
        relative = report_dir.resolve().relative_to(ccn_root.resolve())
        error = category_path_error(relative.parent.as_posix(), category)
    except ValueError as exc:
        raise DeliverableValidationError(str(exc)) from exc
    if error:
        raise DeliverableValidationError(error)


def validate_tasks(tasks: list[dict[str, Any]], ccn_root: Path) -> list[TaskValidation]:
    task_ids = [task["task_id"] for task in tasks]
    directory_matches = map_task_directories(ccn_root, task_ids)
    results: list[TaskValidation] = []
    current_dirs: set[Path] = set()
    for task_id in task_ids:
        matches = directory_matches[task_id]
        if len(matches) != 1:
            results.append(
                TaskValidation(
                    task_id=task_id,
                    errors=[f"根据 README 精确任务编号找到 {len(matches)} 个正式报告目录，要求恰好 1 个"],
                )
            )
        else:
            current_dirs.add(matches[0])

    history = historical_basenames(ccn_root, current_dirs)
    result_by_id = {result.task_id: result for result in results}
    for task_id in task_ids:
        matches = directory_matches[task_id]
        if len(matches) == 1:
            result_by_id[task_id] = validate_report_directory(
                matches[0], task_id, historical_basenames=history
            )
    results = [result_by_id[task_id] for task_id in task_ids]
    for task, result in zip(tasks, results):
        if result.report_dir:
            try:
                validate_category_constraint(result.report_dir, ccn_root, task.get('category'))
            except DeliverableValidationError as exc:
                result.errors.append(str(exc))

    by_basename: dict[str, list[TaskValidation]] = {}
    for result in results:
        if result.basename:
            by_basename.setdefault(result.basename.casefold(), []).append(result)
    for duplicates in by_basename.values():
        if len(duplicates) > 1:
            task_list = ", ".join(result.task_id for result in duplicates)
            for result in duplicates:
                result.errors.append(f"主题短名在当前批次内重复：{task_list}")
    return results


def validate_completion_report(report_dir: Path, task_id: str, ccn_root: Path) -> str:
    report_dir = report_dir.resolve()
    ccn_root = ccn_root.resolve()
    current_dirs = {report_dir}
    history = (
        historical_basenames(ccn_root, current_dirs)
        if ccn_root.is_dir() and report_dir.is_relative_to(ccn_root)
        else set()
    )
    result = validate_report_directory(
        report_dir, task_id, historical_basenames=history
    )
    if result.errors:
        raise DeliverableValidationError("；".join(result.errors))
    assert result.basename is not None
    return result.basename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="校验 CCN Loop 本轮正式交付件命名与 README 链接。")
    parser.add_argument("--tasks", required=True, type=Path, help="本轮工作队列 JSON")
    parser.add_argument("--ccn-root", required=True, type=Path, help="ccn-report 根目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        tasks = load_tasks(args.tasks.resolve())
        results = validate_tasks(tasks, args.ccn_root.resolve())
    except (DeliverableValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    failed = False
    for result in results:
        location = str(result.report_dir) if result.report_dir else "<未找到>"
        name = result.basename or "<无法确定>"
        status = "FAIL" if result.errors else "PASS"
        print(f"[{status}] {result.task_id} -> {name} ({location})")
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        failed = failed or bool(result.errors)
    print(f"校验完成：{len(results) - sum(bool(item.errors) for item in results)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
