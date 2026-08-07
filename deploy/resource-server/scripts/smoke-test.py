#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


def fetch(url: str, *, token: str | None = None, method: str = "GET", payload: object | None = None, idem: str | None = None) -> dict[str, object]:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"User-Agent": "mozhi-resource-server-smoke/1.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if idem:
        headers["Idempotency-Key"] = idem
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
        if response.status >= 400:
            raise RuntimeError(f"{url} returned {response.status}")
        if not data:
            return {}
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {"status": "success", "content_length": len(data)}


def internal_check() -> None:
    checks = [
        ["docker", "exec", "mozhi-agent-workspace-docs", "wget", "-q", "-O", "-", "http://127.0.0.1:8080/healthz"],
        ["docker", "exec", "ccn-brief-task-api", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"],
    ]
    available = 0
    for command in checks:
        inspect = subprocess.run(["docker", "inspect", command[2]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if inspect.returncode:
            continue
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
        available += 1
    if not available:
        raise SystemExit("No managed service containers were available for internal checks")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the resource server and CCN API.")
    parser.add_argument("--api-base", default="https://ccn-api.haohaoxiaoyu.top")
    parser.add_argument("--docs-base", default="https://docs.haohaoxiaoyu.top")
    parser.add_argument("--api-key", default=os.environ.get("CCN_API_KEY"))
    parser.add_argument("--internal", action="store_true")
    parser.add_argument("--skip-write", action="store_true")
    args = parser.parse_args()

    if args.internal:
        internal_check()
        print("internal smoke checks passed")
        return 0

    fetch(args.docs_base.rstrip("/") + "/")
    fetch(args.api_base.rstrip("/") + "/healthz")
    if args.skip_write:
        print("public read-only smoke checks passed")
        return 0
    if not args.api_key:
        raise SystemExit("CCN_API_KEY is required for write smoke tests")

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d%H%M%S")
    task_id = f"SMOKE-{stamp}"
    task = {
        "task_id": task_id,
        "content": "resource server deployment smoke test",
        "url": "https://example.com/ccn-smoke-source",
        "hotspot_id": "SMOKE",
        "period": stamp[:8],
    }
    created = fetch(
        args.api_base.rstrip("/") + "/api/v1/tasks",
        token=args.api_key,
        method="POST",
        payload=task,
        idem=f"create-{task_id}",
    )
    assert created.get("status") == "success"
    fetched = fetch(args.api_base.rstrip("/") + f"/api/v1/tasks/{task_id}", token=args.api_key)
    assert fetched.get("status") == "success"
    pending = fetch(
        args.api_base.rstrip("/")
        + f"/api/v1/tasks?status=pending&q={task_id}&hotspot_id=SMOKE&period={stamp[:8]}",
        token=args.api_key,
    )
    assert any(item.get("task_id") == task_id for item in pending.get("data", []))
    result = fetch(
        args.api_base.rstrip("/") + f"/api/v1/tasks/{task_id}/results",
        token=args.api_key,
        method="POST",
        payload={"outcome": "completed", "summary": "smoke test passed"},
        idem=f"result-{task_id}",
    )
    assert result.get("status") == "success"
    completed = fetch(
        args.api_base.rstrip("/") + f"/api/v1/tasks?status=completed&q={task_id}",
        token=args.api_key,
    )
    assert any(item.get("task_id") == task_id for item in completed.get("data", []))
    deleted = fetch(
        args.api_base.rstrip("/") + "/api/v1/tasks",
        token=args.api_key,
        method="DELETE",
        payload={"task_ids": [task_id, f"{task_id}-MISSING"]},
    )
    assert deleted.get("data") == {
        "requested": 2,
        "deleted": 1,
        "missing": [f"{task_id}-MISSING"],
    }
    repeated_delete = fetch(
        args.api_base.rstrip("/") + f"/api/v1/tasks/{task_id}",
        token=args.api_key,
        method="DELETE",
    )
    assert repeated_delete.get("data") == {"task_id": task_id, "deleted": False}
    print(json.dumps({"status": "success", "task_id": task_id}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (urllib.error.URLError, RuntimeError, AssertionError) as exc:
        print(f"smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
