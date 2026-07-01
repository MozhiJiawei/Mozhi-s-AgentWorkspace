from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


START_MARKER = "<!-- guardian-findings:start -->"
END_MARKER = "<!-- guardian-findings:end -->"
DEFAULT_ISSUE = 12
STATUS_PENDING = "待处理"
STATUS_CLOSED = "已关闭"
STATUS_IGNORED = "已忽略"
SEVERITY_P0 = "P0"
SEVERITY_P1 = "P1"
SEVERITY_P2 = "P2"
FIELD_STATUS = "状态"
FIELD_SEVERITY = "严重级别"
FIELD_TARGET = "目标"
FIELD_PAGE_URL = "页面链接"
FIELD_PROBLEM = "问题描述"
FIELD_ROOT_CAUSE = "代码根因"
FIELD_FIRST_SEEN = "首次发现"
FIELD_LAST_SEEN = "最近发现"
FIELD_EVIDENCE = "证据"
FIELD_NOTE = "处理建议"
FIELD_UPDATED_BY = "更新人"
FIELD_UPDATED_AT = "更新时间"
FIELD_RESOLUTION = "处理结论"
FIELD_ORDER = [
    FIELD_STATUS,
    FIELD_SEVERITY,
    FIELD_TARGET,
    FIELD_PAGE_URL,
    FIELD_PROBLEM,
    FIELD_ROOT_CAUSE,
    FIELD_FIRST_SEEN,
    FIELD_LAST_SEEN,
    FIELD_EVIDENCE,
    FIELD_NOTE,
    FIELD_UPDATED_BY,
    FIELD_UPDATED_AT,
    FIELD_RESOLUTION,
]
CANONICAL_PREFIX = """# Material Quality Guardian

## 状态协议

- `待处理`：当前仍需要关注或处理的问题。
- `已忽略`：人类或其他修复 Agent 确认不需要继续处理、但需要保留抑制记录的问题。
- `严重级别`：`P0` / `P1` / `P2`，表示修复优先级；严重级别不替代状态。
- `P0`：资料入口、发布可信度或核心交付链路整体不可用，或验证机制会明显误判成功。
- `P1`：单个 workspace/skill 的重要使用路径会失败，或文档与实现契约明显不一致。
- `P2`：局部资料质量问题，不阻断主要使用路径，但影响可读性、维护性或后续审查效率。
- 每个 finding 必须包含 `问题描述`、`页面链接` 和 `代码根因`：问题描述给人类快速判断，页面链接用于打开有问题的资料页，代码根因承载路径、脚本输出、HTTP 状态、指纹等技术细节。
- 已完成的 finding 必须通过 `python loops/material-quality-guardian/issue_db.py delete <id>` 从 Issue 中移除。
- 所有 finding 状态变更必须通过 `python loops/material-quality-guardian/issue_db.py status ...` 或 `delete` 写回 Issue body。
- Guardian Loop 每轮通过 `python loops/material-quality-guardian/issue_db.py list` 读取历史 Issue 状态，并通过 `upsert` 新增或刷新 `待处理` 问题。
- Guardian Loop 不负责修复，也不负责把问题改成 `已忽略`；读取到 `已关闭` finding 时应清理删除。
- Guardian Loop 不回复 Issue，不追加评论；Issue body 是唯一状态面。
- 人类或其他修复 Agent 修复完成后必须用 `issue_db.py delete` 删除问题；确认无需处理时用 `issue_db.py status` 标记为 `已忽略` 并填写 `更新人`、`更新时间`、`处理结论`。
- 不要手写 Issue markdown，也不要通过 Issue 评论表达状态变更；如果脚本不可用，应先修复脚本或停止并报告。"""


@dataclass
class Finding:
    id: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return self.fields.get(FIELD_STATUS, STATUS_PENDING)


def run_gh(args: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["gh", *args],
        input=input_text,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"gh 命令执行失败: {' '.join(args)}")
    return result.stdout


def current_repo() -> str:
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if remote.returncode != 0:
        raise SystemExit("无法从 git origin 推断 GitHub 仓库，请显式传入 --repo owner/name。")
    url = remote.stdout.strip()
    match = re.search(r"github\.com[:/](?P<repo>[^/]+/[^/.]+)(?:\.git)?$", url)
    if not match:
        raise SystemExit(f"无法从 origin URL 推断 GitHub 仓库：{url}")
    return match.group("repo")


def read_issue_body(repo: str, issue: int) -> str:
    payload = run_gh(["issue", "view", str(issue), "--repo", repo, "--json", "body"])
    body = json.loads(payload)["body"] or ""
    return body.replace("\r\n", "\n").replace("\r", "\n")


def write_issue_body(repo: str, issue: int, body: str) -> None:
    run_gh(["issue", "edit", str(issue), "--repo", repo, "--body-file", "-"], input_text=body)


def split_body(body: str) -> tuple[str, str, str]:
    start = body.find(START_MARKER)
    end = body.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(
            f"Issue body 必须同时包含这两个标记：{START_MARKER} 和 {END_MARKER}"
        )
    end += len(END_MARKER)
    return body[:start], body[start:end], body[end:]


def parse_findings(section: str) -> list[Finding]:
    content = section
    content = content.replace(START_MARKER, "").replace(END_MARKER, "")
    blocks = re.split(r"(?m)^###\s+", content)
    findings: list[Finding] = []
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        finding_id = lines[0].strip()
        fields: dict[str, str] = {}
        for line in lines[1:]:
            match = re.match(r"^-\s*([^:：]+)\s*[:：]\s*(.*)\s*$", line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                if key == FIELD_STATUS:
                    value = validate_status(value)
                elif key == FIELD_SEVERITY:
                    value = validate_severity(value)
                fields[key] = value
        findings.append(Finding(finding_id, fields))
    return findings


def render_findings(findings: list[Finding]) -> str:
    lines = [START_MARKER, "## 问题列表", ""]
    if not findings:
        lines.append("本轮尚未登记资料刷新问题。")
    for finding in findings:
        lines.append(f"### {finding.id}")
        lines.append("")
        for key in FIELD_ORDER:
            if key in finding.fields and finding.fields[key] != "":
                lines.append(f"- {key}: {finding.fields[key]}")
        for key in sorted(k for k in finding.fields if k not in FIELD_ORDER):
            if finding.fields[key] != "":
                lines.append(f"- {key}: {finding.fields[key]}")
        lines.append("")
    if lines[-1] == "":
        lines.pop()
    lines.append(END_MARKER)
    return "\n".join(lines)


def load_db(repo: str, issue: int) -> tuple[str, list[Finding], str]:
    body = read_issue_body(repo, issue)
    prefix, section, suffix = split_body(body)
    return prefix, parse_findings(section), suffix


def save_db(repo: str, issue: int, prefix: str, findings: list[Finding], suffix: str) -> None:
    body = prefix.rstrip() + "\n\n" + render_findings(findings) + "\n" + suffix.lstrip()
    body = re.sub(r"\n{3,}", "\n\n", body)
    write_issue_body(repo, issue, body)


def find_index(findings: list[Finding], finding_id: str) -> int | None:
    for index, finding in enumerate(findings):
        if finding.id == finding_id:
            return index
    return None


def validate_status(status: str) -> str:
    if status not in {STATUS_PENDING, STATUS_CLOSED, STATUS_IGNORED}:
        raise SystemExit(f"状态必须是以下之一：{STATUS_PENDING}、{STATUS_CLOSED}、{STATUS_IGNORED}")
    return status


def validate_severity(severity: str) -> str:
    if severity not in {SEVERITY_P0, SEVERITY_P1, SEVERITY_P2}:
        raise SystemExit(f"严重级别必须是以下之一：{SEVERITY_P0}、{SEVERITY_P1}、{SEVERITY_P2}")
    return severity


def cmd_list(args: argparse.Namespace) -> None:
    _, findings, _ = load_db(args.repo, args.issue)
    print(json.dumps([{"问题ID": f.id, **f.fields} for f in findings], ensure_ascii=False, indent=2))


def cmd_get(args: argparse.Namespace) -> None:
    _, findings, _ = load_db(args.repo, args.issue)
    index = find_index(findings, args.id)
    if index is None:
        raise SystemExit(f"未找到问题：{args.id}")
    finding = findings[index]
    print(json.dumps({"问题ID": finding.id, **finding.fields}, ensure_ascii=False, indent=2))


def cmd_upsert(args: argparse.Namespace) -> None:
    prefix, findings, suffix = load_db(args.repo, args.issue)
    index = find_index(findings, args.id)
    today = date.today().isoformat()
    if index is None:
        finding = Finding(
            args.id,
            {
                FIELD_STATUS: STATUS_PENDING,
                FIELD_SEVERITY: validate_severity(args.severity),
                FIELD_TARGET: args.target,
                FIELD_PAGE_URL: args.page_url,
                FIELD_PROBLEM: args.problem,
                FIELD_ROOT_CAUSE: args.root_cause,
                FIELD_FIRST_SEEN: args.first_seen or today,
                FIELD_LAST_SEEN: args.last_seen or today,
                FIELD_EVIDENCE: args.evidence,
                FIELD_NOTE: args.note,
            },
        )
        findings.append(finding)
    else:
        finding = findings[index]
        if finding.status == STATUS_PENDING:
            finding.fields.update(
                {
                    FIELD_SEVERITY: validate_severity(args.severity),
                    FIELD_TARGET: args.target,
                    FIELD_PAGE_URL: args.page_url,
                    FIELD_PROBLEM: args.problem,
                    FIELD_ROOT_CAUSE: args.root_cause,
                    FIELD_LAST_SEEN: args.last_seen or today,
                    FIELD_EVIDENCE: args.evidence,
                    FIELD_NOTE: args.note,
                }
            )
            finding.fields.setdefault(FIELD_FIRST_SEEN, args.first_seen or today)
        else:
            finding.fields.setdefault(FIELD_LAST_SEEN, args.last_seen or today)
    save_db(args.repo, args.issue, prefix, findings, suffix)
    print(f"已写入问题 {args.id}（{findings[find_index(findings, args.id)].status}）")


def cmd_status(args: argparse.Namespace) -> None:
    prefix, findings, suffix = load_db(args.repo, args.issue)
    index = find_index(findings, args.id)
    if index is None:
        raise SystemExit(f"未找到问题：{args.id}")
    status = validate_status(args.status)
    finding = findings[index]
    finding.fields[FIELD_STATUS] = status
    if args.updated_by:
        finding.fields[FIELD_UPDATED_BY] = args.updated_by
    if args.updated_at:
        finding.fields[FIELD_UPDATED_AT] = args.updated_at
    elif status in {STATUS_CLOSED, STATUS_IGNORED}:
        finding.fields[FIELD_UPDATED_AT] = date.today().isoformat()
    if args.resolution:
        finding.fields[FIELD_RESOLUTION] = args.resolution
    save_db(args.repo, args.issue, prefix, findings, suffix)
    print(f"已更新问题 {args.id} -> {status}")


def cmd_delete(args: argparse.Namespace) -> None:
    prefix, findings, suffix = load_db(args.repo, args.issue)
    index = find_index(findings, args.id)
    if index is None:
        raise SystemExit(f"未找到问题：{args.id}")
    del findings[index]
    save_db(args.repo, args.issue, prefix, findings, suffix)
    print(f"已删除问题 {args.id}")


def cmd_sync_protocol(args: argparse.Namespace) -> None:
    _, findings, suffix = load_db(args.repo, args.issue)
    save_db(args.repo, args.issue, CANONICAL_PREFIX, findings, suffix)
    print("已同步 Issue 状态协议")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="把 Material Quality Guardian 的 GitHub Issue 当作轻量问题库来维护。"
    )
    parser.add_argument("--repo", default=None, help="GitHub 仓库，例如 MozhiJiawei/Mozhi-s-AgentWorkspace")
    parser.add_argument("--issue", type=int, default=DEFAULT_ISSUE, help="GitHub Issue 编号")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="以 JSON 列出问题")
    list_parser.set_defaults(func=cmd_list)

    get_parser = subparsers.add_parser("get", help="以 JSON 读取单个问题")
    get_parser.add_argument("id")
    get_parser.set_defaults(func=cmd_get)

    upsert_parser = subparsers.add_parser("upsert", help="新增或刷新一个待处理问题")
    upsert_parser.add_argument("--id", required=True)
    upsert_parser.add_argument("--target", required=True)
    upsert_parser.add_argument("--page-url", required=True)
    upsert_parser.add_argument("--problem", required=True)
    upsert_parser.add_argument("--root-cause", required=True)
    upsert_parser.add_argument("--severity", default=SEVERITY_P1, choices=[SEVERITY_P0, SEVERITY_P1, SEVERITY_P2])
    upsert_parser.add_argument("--evidence", required=True)
    upsert_parser.add_argument("--note", required=True)
    upsert_parser.add_argument("--first-seen")
    upsert_parser.add_argument("--last-seen")
    upsert_parser.set_defaults(func=cmd_upsert)

    status_parser = subparsers.add_parser("status", help="更新问题状态")
    status_parser.add_argument("id")
    status_parser.add_argument("status", choices=[STATUS_PENDING, STATUS_CLOSED, STATUS_IGNORED])
    status_parser.add_argument("--updated-by")
    status_parser.add_argument("--updated-at")
    status_parser.add_argument("--resolution")
    status_parser.set_defaults(func=cmd_status)

    delete_parser = subparsers.add_parser("delete", help="从 Issue 数据库中删除一个问题")
    delete_parser.add_argument("id")
    delete_parser.set_defaults(func=cmd_delete)

    sync_protocol_parser = subparsers.add_parser("sync-protocol", help="同步 Issue body 中 marker 外的状态协议")
    sync_protocol_parser.set_defaults(func=cmd_sync_protocol)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.repo = args.repo or current_repo()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
