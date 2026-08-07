from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

import requests

from task_service.app.domain.percent_encoding import decode_non_ascii_percent_escapes
from task_service.app.domain.task_contract import TASK_ID_PATTERN, is_valid_https_url


LOOP_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = LOOP_ROOT.parent.parent
DEFAULT_CONFIG = LOOP_ROOT / "config.json"
DEFAULT_CREDENTIALS = Path.home() / ".ccn-brief-report" / "client.json"
DEFAULT_OUTPUT = WORKSPACE_ROOT / ".tmp" / "loops" / "ccn-brief-report" / "tasks.json"
DEFAULT_REJECTED_OUTPUT = WORKSPACE_ROOT / ".tmp" / "loops" / "ccn-brief-report" / "rejected-tasks.json"
DEFAULT_STATE = WORKSPACE_ROOT / ".tmp" / "loops" / "ccn-brief-report" / "state.json"
REQUIRED_FIELDS = ("row_number", "task_id", "content", "url", "hotspot_id", "period")
TEXT_FIELDS = ("task_id", "content", "url", "hotspot_id", "period")


class TaskAPIError(RuntimeError):
    pass


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TaskAPIError("config.json 顶层必须是对象")
    return payload


def api_base(config: dict[str, Any]) -> str:
    value = os.environ.get("CCN_BRIEF_TASK_API_BASE") or config.get("api_base")
    if not isinstance(value, str) or not value.startswith("https://"):
        raise TaskAPIError("任务 API 必须是有效的 HTTPS 地址")
    parsed = urlsplit(value)
    if not parsed.netloc or parsed.query or parsed.fragment:
        raise TaskAPIError("任务 API 地址格式无效")
    return value.rstrip("/")


def credentials_path() -> Path:
    configured = os.environ.get("CCN_BRIEF_TASK_API_CONFIG")
    return Path(configured).expanduser() if configured else DEFAULT_CREDENTIALS


def load_credentials(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TaskAPIError("私有凭据文件顶层必须是对象")
    return payload


def api_key(credentials: dict[str, Any]) -> str:
    value = os.environ.get("CCN_API_KEY") or credentials.get("api_key")
    if not isinstance(value, str) or len(value.strip()) < 32:
        raise TaskAPIError(
            "缺少 CCN API Key；请设置 CCN_API_KEY，或写入私有文件 "
            f"{credentials_path()}"
        )
    return value.strip()


def normalize_task(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise TaskAPIError(f"第 {index} 条任务不是对象")
    missing = [field for field in REQUIRED_FIELDS if raw.get(field) in (None, "")]
    if missing:
        raise TaskAPIError(f"第 {index} 条任务缺少字段：{', '.join(missing)}")
    try:
        row_number = int(raw["row_number"])
    except (TypeError, ValueError) as exc:
        raise TaskAPIError(f"第 {index} 条任务 row_number 不是整数") from exc
    if row_number < 1:
        raise TaskAPIError(f"第 {index} 条任务 row_number 必须大于 0")
    invalid_types = [field for field in TEXT_FIELDS if not isinstance(raw[field], str)]
    if invalid_types:
        raise TaskAPIError(f"第 {index} 条任务字段必须是字符串：{', '.join(invalid_types)}")
    if not TASK_ID_PATTERN.fullmatch(raw["task_id"]):
        raise TaskAPIError(f"第 {index} 条任务 task_id 格式无效")
    if not is_valid_https_url(raw["url"]):
        raise TaskAPIError(f"第 {index} 条任务 url 必须是有效的 HTTPS 地址")
    task = {field: raw[field] for field in REQUIRED_FIELDS}
    task["row_number"] = row_number
    task["status"] = raw.get("status") or ""
    return task


def deduplicate_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    comparison_fields = ("row_number", "content", "url", "hotspot_id", "period")
    for task in tasks:
        task_id = task["task_id"]
        existing = unique.get(task_id)
        if existing is None:
            unique[task_id] = task
            continue
        if any(existing[field] != task[field] for field in comparison_fields):
            raise TaskAPIError(f"任务编号 {task_id} 存在内容冲突的重复记录")
    return list(unique.values())


def fetch_tasks(
    *,
    base_url: str,
    key: str,
    timeout: float,
    session: requests.sessions.Session | None = None,
    rejected: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    requester = session or requests
    headers = {"Authorization": f"Bearer {key}"}
    params: dict[str, str | int] = {"status": "pending", "limit": 500}
    raw_tasks: list[Any] = []
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
            raise TaskAPIError(f"任务接口请求失败：{exc}") from exc
        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise TaskAPIError("任务接口返回失败")
        data = payload.get("data") or []
        if not isinstance(data, list):
            raise TaskAPIError("任务接口 data 必须是数组")
        raw_tasks.extend(data)
        pagination = payload.get("pagination") or {}
        if not isinstance(pagination, dict) or not pagination.get("has_more"):
            break
        next_cursor = pagination.get("next_cursor")
        if not isinstance(next_cursor, int) or next_cursor < 1:
            raise TaskAPIError("任务接口分页游标无效")
        if next_cursor in seen_cursors:
            raise TaskAPIError("任务接口分页游标没有前进")
        seen_cursors.add(next_cursor)
        params["cursor"] = next_cursor
    tasks = []
    for index, item in enumerate(raw_tasks, start=1):
        try:
            tasks.append(normalize_task(item, index))
        except TaskAPIError as exc:
            if rejected is None:
                raise
            task_id = item.get("task_id") if isinstance(item, dict) else None
            rejected.append({"index": index, "task_id": task_id, "error": str(exc)})
    tasks.sort(key=lambda item: (item["row_number"], str(item["task_id"])))
    return deduplicate_tasks(tasks)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_fetch(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config))
    credentials = load_credentials(Path(args.credentials))
    timeout = float(config.get("request_timeout_seconds", 30))
    rejected: list[dict[str, Any]] = []
    tasks = fetch_tasks(
        base_url=api_base(config),
        key=api_key(credentials),
        timeout=timeout,
        rejected=rejected,
    )
    output = Path(args.output).resolve()
    rejected_output = Path(args.rejected_output).resolve()
    write_json(output, tasks)
    write_json(rejected_output, rejected)
    print(
        json.dumps(
            {
                "status": "success",
                "count": len(tasks),
                "rejected": len(rejected),
                "output": str(output),
                "rejected_output": str(rejected_output),
            },
            ensure_ascii=False,
        )
    )
    return 0


def validate_artifact_url(value: str, config: dict[str, Any]) -> str:
    repository = config.get("ccn_report_repository_url")
    if not isinstance(repository, str):
        raise TaskAPIError("config.json 缺少 ccn_report_repository_url")
    expected = urlsplit(repository.rstrip("/"))
    parsed = urlsplit(value)
    expected_prefix = expected.path.rstrip("/") + "/tree/main/"
    decoded_path = unquote(parsed.path)
    iri_path = decode_non_ascii_percent_escapes(parsed.path)
    relative_path = decoded_path[len(expected_prefix):] if decoded_path.startswith(expected_prefix) else ""
    path_segments = relative_path.split("/")
    if (
        parsed.scheme != "https"
        or parsed.netloc != expected.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not decoded_path.startswith(expected_prefix)
        or decoded_path == expected_prefix
        or any(segment in {"", ".", ".."} for segment in path_segments)
    ):
        raise TaskAPIError("结果 URL 必须是 ccn-report main 分支中的报告目录直达地址")
    return urlunsplit((parsed.scheme, parsed.netloc, iri_path, "", ""))


def fetch_task(*, base_url: str, key: str, task_id: str, timeout: float, session=None) -> dict[str, Any]:
    requester = session or requests
    try:
        response = requester.get(
            f"{base_url}/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {key}"},
            timeout=(5, timeout),
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise TaskAPIError(f"任务状态查询失败：{exc}") from exc
    if not isinstance(payload, dict) or payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
        raise TaskAPIError("任务状态接口返回失败")
    return payload["data"]


def result_matches(task: dict[str, Any], artifact_url: str) -> bool:
    result = task.get("latest_result")
    return (
        task.get("status") == "completed"
        and isinstance(result, dict)
        and result.get("outcome") == "completed"
        and result.get("artifact_urls") == [artifact_url]
    )


def submit_result(*, base_url: str, key: str, task_id: str, artifact_url: str, timeout: float, session=None) -> dict[str, Any]:
    requester = session or requests
    payload = {"outcome": "completed", "artifact_urls": [artifact_url]}
    digest = hashlib.sha256(artifact_url.encode("utf-8")).hexdigest()[:16]
    headers = {
        "Authorization": f"Bearer {key}",
        "Idempotency-Key": f"ccn-report-{task_id}-{digest}",
    }
    try:
        response = requester.post(
            f"{base_url}/api/v1/tasks/{task_id}/results",
            headers=headers,
            json=payload,
            timeout=(5, timeout),
        )
        response.raise_for_status()
    except requests.RequestException:
        task = fetch_task(
            base_url=base_url,
            key=key,
            task_id=task_id,
            timeout=timeout,
            session=requester,
        )
        if result_matches(task, artifact_url):
            return task
        raise TaskAPIError("结果提交状态不确定，服务端对账未确认成功")
    task = fetch_task(
        base_url=base_url,
        key=key,
        task_id=task_id,
        timeout=timeout,
        session=requester,
    )
    if not result_matches(task, artifact_url):
        raise TaskAPIError("结果提交后服务端状态或 URL 不匹配")
    return task


def cmd_complete(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config))
    credentials = load_credentials(Path(args.credentials))
    timeout = float(config.get("request_timeout_seconds", 30))
    task_id = args.task_id
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise TaskAPIError("task_id 格式无效")
    artifact_url = validate_artifact_url(args.artifact_url, config)
    report_path = Path(args.report_path).resolve()
    if not report_path.is_dir():
        raise TaskAPIError("本地报告目录不存在")
    task = submit_result(
        base_url=api_base(config),
        key=api_key(credentials),
        task_id=task_id,
        artifact_url=artifact_url,
        timeout=timeout,
    )
    import local_state

    record = local_state.record_completed_task(
        Path(args.state),
        task_id=task_id,
        report_path=str(report_path),
        artifact_url=artifact_url,
    )
    print(
        json.dumps(
            {
                "status": "success",
                "task_id": task_id,
                "remote_status": task["status"],
                "artifact_url": artifact_url,
                "local_status": record["status"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从 CCN 任务 API 读取待处理快报任务。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--credentials", default=str(credentials_path()))
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch_parser = subparsers.add_parser("fetch", help="拉取并标准化全部未领取任务")
    fetch_parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    fetch_parser.add_argument("--rejected-output", default=str(DEFAULT_REJECTED_OUTPUT))
    fetch_parser.set_defaults(func=cmd_fetch)
    complete_parser = subparsers.add_parser("complete", help="幂等回传结果、对账并标记本地完成")
    complete_parser.add_argument("--task-id", required=True)
    complete_parser.add_argument("--artifact-url", required=True)
    complete_parser.add_argument("--report-path", required=True)
    complete_parser.add_argument("--state", default=str(DEFAULT_STATE))
    complete_parser.set_defaults(func=cmd_complete)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (TaskAPIError, OSError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
