from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any
from urllib.parse import urlunsplit

import requests

import task_api


HTML_PREFERRED_NAMES = ("source_understanding_review.html", "source_understanding.html")
PPTX_PREFERRED_NAMES = ("single_page_tech_report.pptx",)


def fetch_completed_tasks(
    *,
    base_url: str,
    key: str,
    timeout: float,
    session=None,
) -> list[dict[str, Any]]:
    requester = session or requests
    headers = {"Authorization": f"Bearer {key}"}
    params: dict[str, str | int] = {"status": "completed", "limit": 500}
    tasks: list[dict[str, Any]] = []
    seen_cursors: set[int] = set()
    while True:
        try:
            response = requester.get(
                f"{base_url}/api/v1/tasks",
                headers=headers,
                params=params,
                timeout=(5, timeout),
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise task_api.TaskAPIError(f"已完成任务查询失败：{exc}") from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(payload, dict) or payload.get("status") != "success" or not isinstance(data, list):
            raise task_api.TaskAPIError("已完成任务接口返回失败")
        tasks.extend(item for item in data if isinstance(item, dict))
        pagination = payload.get("pagination") or {}
        if not pagination.get("has_more"):
            return tasks
        next_cursor = pagination.get("next_cursor")
        if not isinstance(next_cursor, int) or next_cursor < 1 or next_cursor in seen_cursors:
            raise task_api.TaskAPIError("已完成任务接口分页游标无效")
        seen_cursors.add(next_cursor)
        params["cursor"] = next_cursor


def choose_file(report_dir: Path, preferred_names: tuple[str, ...], suffix: str) -> Path | None:
    for name in preferred_names:
        candidate = report_dir / name
        if candidate.is_file():
            return candidate
    candidates = sorted(path for path in report_dir.glob(f"*{suffix}") if path.is_file())
    return candidates[0] if len(candidates) == 1 else None


def report_directory(task: dict[str, Any], ccn_root: Path, config: dict[str, Any]) -> tuple[str, Path] | None:
    result = task.get("latest_result")
    urls = result.get("artifact_urls") if isinstance(result, dict) else None
    if not isinstance(urls, list) or not urls or not isinstance(urls[0], str):
        return None
    artifact_url = task_api.validate_artifact_url(urls[0], config)
    relative = task_api.report_relative_path(artifact_url, config)
    parts = PurePosixPath(relative).parts
    report_dir = ccn_root.joinpath(*parts).resolve()
    try:
        report_dir.relative_to(ccn_root.resolve())
    except ValueError as exc:
        raise task_api.TaskAPIError(f"任务 {task.get('task_id')} 的报告路径越出 ccn-report") from exc
    return artifact_url, report_dir


def download_url(config: dict[str, Any], relative_path: str, filename: str) -> str:
    repository = task_api.configured_repository(config)
    path = repository.path.rstrip("/") + "/raw/refs/heads/main/" + relative_path.rstrip("/") + "/" + filename
    return urlunsplit((repository.scheme, repository.netloc, path, "download=1", ""))


def artifact_urls_for_task(
    task: dict[str, Any],
    *,
    ccn_root: Path,
    config: dict[str, Any],
) -> list[str] | None:
    located = report_directory(task, ccn_root, config)
    if located is None:
        return None
    artifact_url, report_dir = located
    if not report_dir.is_dir():
        return None
    relative = task_api.report_relative_path(artifact_url, config)
    html = choose_file(report_dir, HTML_PREFERRED_NAMES, ".html")
    if html is None:
        return None
    urls = [artifact_url, download_url(config, relative, html.name)]
    pptx = choose_file(report_dir, PPTX_PREFERRED_NAMES, ".pptx")
    if pptx is not None:
        urls.append(download_url(config, relative, pptx.name))
    return urls


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="为历史 CCN 完成记录一次性回填 HTML/PPTX Git LFS 下载链接。默认仅预演。"
    )
    parser.add_argument("--config", default=str(task_api.DEFAULT_CONFIG))
    parser.add_argument("--credentials", default=str(task_api.credentials_path()))
    parser.add_argument("--ccn-root", default=str(task_api.WORKSPACE_ROOT / "ccn-report"))
    parser.add_argument("--apply", action="store_true", help="实际追加回填结果；省略时只输出预演。")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = task_api.load_config(Path(args.config))
        credentials = task_api.load_credentials(Path(args.credentials))
        key = task_api.api_key(credentials)
        base_url = task_api.api_base(config)
        timeout = float(config.get("request_timeout_seconds", 30))
        tasks = fetch_completed_tasks(base_url=base_url, key=key, timeout=timeout)
        ccn_root = Path(args.ccn_root).resolve()
        results: list[dict[str, Any]] = []
        for task in tasks:
            current = task.get("latest_result") or {}
            current_urls = current.get("artifact_urls") or []
            urls = artifact_urls_for_task(task, ccn_root=ccn_root, config=config)
            if not urls:
                results.append({"task_id": task.get("task_id"), "status": "no-local-html"})
                continue
            task_api.validate_download_url(
                urls[1],
                config,
                artifact_url=urls[0],
                expected_suffix=".html",
            )
            if len(urls) == 3:
                task_api.validate_download_url(
                    urls[2],
                    config,
                    artifact_url=urls[0],
                    expected_suffix=".pptx",
                )
            if current_urls == urls:
                results.append({"task_id": task.get("task_id"), "status": "already-populated"})
                continue
            status = "would-update"
            if args.apply:
                task_api.submit_result(
                    base_url=base_url,
                    key=key,
                    task_id=task["task_id"],
                    artifact_urls=urls,
                    timeout=timeout,
                )
                status = "updated"
            results.append({"task_id": task.get("task_id"), "status": status, "artifact_urls": urls})
        print(json.dumps({"apply": args.apply, "count": len(results), "results": results}, ensure_ascii=False, indent=2))
        return 0
    except (task_api.TaskAPIError, OSError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
