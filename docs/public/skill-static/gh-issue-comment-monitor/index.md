# GitHub Issue 评论监控

`gh-issue-comment-monitor` 是一个轻量 GitHub Issue 协作 skill，用来让 Agent 只读取本轮需要处理的新评论，而不是反复加载完整 issue 历史。

## 架构概览

这个 skill 的核心是“本地 checkpoint + 本轮 updates 文件”：

| 模块 | 职责 |
| --- | --- |
| `SKILL.md` | 定义触发场景、上下文纪律和脚本调用原则。 |
| `scripts/check_issue_updates.py` | 只检查 checkpoint 之后是否有新评论，不更新状态。 |
| `scripts/get_latest_comments.py` | 获取 checkpoint 或指定 comment id 之后的评论，可在处理成功后更新状态。 |
| `scripts/github_issue_comments.py` | 封装 GitHub REST API / `gh api` fallback、评论规范化、状态读写和错误 JSON。 |
| `verify_dependencies.py` | 编译脚本并检查 GitHub API 访问前置条件。 |

## 数据流

```text
GitHub Issue
  -> check_issue_updates.py / get_latest_comments.py
  -> .tmp/gh-issue-comment-monitor/<issue>-updates.json
  -> Agent 读取本轮新增评论
  -> 处理成功后更新 .tmp/gh-issue-comment-monitor/<issue>.json checkpoint
```

## 设计边界

- 只读取评论，不修改 GitHub Issue。
- checkpoint 只记录最后处理到的位置，不保存完整评论正文。
- updates 文件只保存本次返回的评论，不做累计归档。
- 当任务只是“看最新回复”时，优先读取增量；只有缺少 checkpoint 或需要重建背景时才拉完整上下文。

## 输出契约

`check_issue_updates.py` 会返回 `has_updates`、`new_comments`、`latest_comment` 和 `recommended_checkpoint`，但不会更新状态。

`get_latest_comments.py` 会返回 `comments`、`previous_checkpoint`、`next_checkpoint` 和 `state_updated`。只有调用方明确要求更新状态时，才会写回 checkpoint。

推荐产物都写在主工作区 `.tmp/gh-issue-comment-monitor/` 下：

```text
.tmp/gh-issue-comment-monitor/
|-- OWNER-REPO-ISSUE.json
`-- OWNER-REPO-ISSUE-updates.json
```
