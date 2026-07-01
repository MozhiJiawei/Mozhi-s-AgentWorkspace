from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.error
import urllib.request

from docs_publish_state import ROOT, collect_publish_state


DEFAULT_REMOTE_BASE_URL = "http://docs.haohaoxiaoyu.top:8888"
DEFAULT_REMOTE_STATE_PATH = "/material-quality/publish-state.json"


class PublishStateFormatError(ValueError):
    pass


def _fetch_json(url: str, timeout: int) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "material-quality-guardian/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        payload = response.read().decode("utf-8")
    trimmed = payload.lstrip()
    if "json" not in content_type.lower() and trimmed.startswith("<"):
        raise PublishStateFormatError(
            f"expected JSON but got {content_type or 'unknown content-type'} from {url}"
        )
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError(f"Remote state at {url} is not a JSON object.")
    return data


def _skill_map(skills: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(skill["name"]): skill for skill in skills}


def compare_publish_state(
    local: dict[str, object],
    remote: dict[str, object],
    *,
    remote_state_url: str,
) -> dict[str, object]:
    findings: list[dict[str, str]] = []

    local_workspace = local.get("workspace_docs", {})
    remote_workspace = remote.get("workspace_docs", {})
    if local_workspace.get("source_fingerprint") != remote_workspace.get("source_fingerprint"):
        findings.append(
            {
                "id": "MQG-published-workspace-docs-stale",
                "target": "docs/",
                "kind": "publish-drift",
                "evidence": (
                    "远端发布的 workspace docs 指纹与本地源码不一致："
                    f" local={local_workspace.get('source_fingerprint')} "
                    f"remote={remote_workspace.get('source_fingerprint')} "
                    f"state={remote_state_url}"
                ),
                "note": "请重新发布文档站，或核对远端是否已加载最新构建。",
            }
        )

    local_skills = _skill_map(local.get("skills", []))
    remote_skills = _skill_map(remote.get("skills", []))
    for name, local_skill in sorted(local_skills.items()):
        remote_skill = remote_skills.get(name)
        if remote_skill is None:
            findings.append(
                {
                    "id": f"MQG-published-{name}-docs-missing",
                    "target": str(local_skill.get("path", name)),
                    "kind": "publish-missing",
                    "evidence": f"远端 publish-state 中缺少 skill `{name}` 的发布记录：state={remote_state_url}",
                    "note": "请确认该 skill 文档是否已经随最新站点发布。",
                }
            )
            continue
        if local_skill.get("source_fingerprint") != remote_skill.get("source_fingerprint"):
            findings.append(
                {
                    "id": f"MQG-published-{name}-docs-stale",
                    "target": str(local_skill.get("path", name)),
                    "kind": "publish-drift",
                    "evidence": (
                        f"远端发布的 skill `{name}` 文档指纹与本地源码不一致："
                        f" local={local_skill.get('source_fingerprint')}"
                        f" remote={remote_skill.get('source_fingerprint')}"
                        f" state={remote_state_url}"
                    ),
                    "note": "请重新发布文档站，或核对该 skill 文档同步是否缺失。",
                }
            )

    status = "ok" if not findings else "drift"
    return {"status": status, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local docs source state with the published remote docs state.")
    parser.add_argument("--remote-base-url", default=DEFAULT_REMOTE_BASE_URL)
    parser.add_argument("--remote-state-path", default=DEFAULT_REMOTE_STATE_PATH)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--fail-on-drift", action="store_true")
    args = parser.parse_args()

    remote_state_url = args.remote_base_url.rstrip("/") + args.remote_state_path
    local = collect_publish_state(ROOT)
    summary: dict[str, object] = {
        "check": "remote-docs-publish-state",
        "remote_state_url": remote_state_url,
        "local_overall_source_fingerprint": local.get("overall_source_fingerprint"),
    }

    try:
        remote = _fetch_json(remote_state_url, args.timeout)
    except urllib.error.HTTPError as exc:
        summary.update(
            {
                "status": "remote-state-missing",
                "findings": [
                    {
                        "id": "MQG-remote-publish-state-missing",
                        "target": remote_state_url,
                        "kind": "publish-observability-gap",
                        "evidence": f"无法读取远端 publish-state：HTTP {exc.code} at {remote_state_url}",
                        "note": "请先部署带 publish-state 元数据的新文档站版本，再进行远端新旧比对。",
                    }
                ],
            }
        )
    except PublishStateFormatError as exc:
        summary.update(
            {
                "status": "remote-state-missing",
                "findings": [
                    {
                        "id": "MQG-remote-publish-state-missing",
                        "target": remote_state_url,
                        "kind": "publish-observability-gap",
                        "evidence": f"远端 publish-state 端点还未接入或返回了 HTML 兜底页：{exc}",
                        "note": "请先部署带 publish-state 元数据的新文档站版本，再进行远端新旧比对。",
                    }
                ],
            }
        )
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "status": "remote-state-unreachable",
                "findings": [
                    {
                        "id": "MQG-remote-publish-state-unreachable",
                        "target": remote_state_url,
                        "kind": "publish-observability-gap",
                        "evidence": f"无法读取远端 publish-state：{exc}",
                        "note": "请检查远端文档站可达性和 publish-state JSON 是否有效。",
                    }
                ],
            }
        )
    else:
        summary.update(compare_publish_state(local, remote, remote_state_url=remote_state_url))
        summary["remote_overall_source_fingerprint"] = remote.get("overall_source_fingerprint")

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[check] remote-docs-publish-state")
    print(f"[target] {remote_state_url}")
    print(f"[status] {summary.get('status')}")
    findings = summary.get("findings", [])
    if isinstance(findings, list) and findings:
        for finding in findings:
            if isinstance(finding, dict):
                print(f"[finding] {finding.get('id')} :: {finding.get('target')}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.fail_on_drift and summary.get("status") != "ok":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
