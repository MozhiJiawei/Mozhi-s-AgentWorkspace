# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 gh-issue-comment-monitor，请先检查它的依赖；如果 GitHub 访问凭据或 gh CLI 没准备好，请告诉我缺什么并帮我处理。
```

## 检查命令

在 workspace 根目录运行：

```powershell
python skills/gh-issue-comment-monitor/verify_dependencies.py
```

## 它会检查什么

| 类型 | 说明 |
| --- | --- |
| GitHub 凭据 | 检查是否存在 `GITHUB_TOKEN`、`GH_TOKEN`，或已登录的 `gh` CLI |
| GitHub API 网络 | 真实读取 Issue 时需要访问 `api.github.com`；需要时可加 `--check-network` |

## 判断标准

`required` 全部为 `ok: true` 表示 GitHub 访问前置条件可用。若缺少 token 或 `gh` 登录状态，请先让 Agent 配好再执行监控任务。脚本编译、checkpoint 文件读写属于仓库内部健康问题，不作为用户依赖配置展示。
