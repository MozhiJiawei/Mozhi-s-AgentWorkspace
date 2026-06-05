# 使用方式

这个 skill 更适合由 Agent 调用，而不是人工反复执行命令。你只需要把目标 issue 和期望说清楚，Agent 会使用子仓脚本读取增量评论，并把临时状态写入主工作区 `.tmp/`。

## 典型 Prompt

- `请检查 MozhiJiawei/Mozhi-s-AgentWorkspace#3 有没有新的 issue 评论，只处理上次之后的新回复。`
- `请读取这个 GitHub Issue 的最新 5 条评论，并在处理完成后更新本地 checkpoint。`
- `请看看这个 issue 有没有新反馈；如果没有新评论，只告诉我当前 checkpoint 没有变化。`

## 推荐流程

1. Agent 从 prompt 或上下文识别 `OWNER/REPO` 和 issue number。
2. Agent 在主工作区准备状态文件：

```text
.tmp/gh-issue-comment-monitor/<owner>-<repo>-<issue>.json
.tmp/gh-issue-comment-monitor/<owner>-<repo>-<issue>-updates.json
```

3. 先检查是否有 checkpoint 之后的新评论。
4. 只读取本轮新评论或必要的最新评论。
5. 完成理解、回复或后续处理后，再更新 checkpoint。

## 脚本入口

检查新评论，不更新 checkpoint：

```powershell
python scripts/check_issue_updates.py `
  --repo OWNER/REPO `
  --issue NUMBER `
  --state-file .tmp/gh-issue-comment-monitor/OWNER-REPO-NUMBER.json `
  --updates-file .tmp/gh-issue-comment-monitor/OWNER-REPO-NUMBER-updates.json
```

读取并在处理完成后更新 checkpoint：

```powershell
python scripts/get_latest_comments.py `
  --repo OWNER/REPO `
  --issue NUMBER `
  --state-file .tmp/gh-issue-comment-monitor/OWNER-REPO-NUMBER.json `
  --updates-file .tmp/gh-issue-comment-monitor/OWNER-REPO-NUMBER-updates.json `
  --limit 5 `
  --update-state
```

## 依赖检查

```powershell
python verify_dependencies.py
```

真实读取 issue 需要 `GITHUB_TOKEN`、`GH_TOKEN`，或已登录的 `gh` CLI。
