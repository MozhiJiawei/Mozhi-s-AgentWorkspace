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
| Python 脚本 | 检查 issue 评论读取脚本是否能正常编译 |
| GitHub 访问 | 检查是否存在 `GITHUB_TOKEN`、`GH_TOKEN`，或可用的 `gh` CLI |
| 网络 | 真实读取 Issue 时需要访问 GitHub API |

## 判断标准

`required` 全部为 `ok: true` 表示脚本本身可用。凭据属于真实访问前置条件；如果检查结果提示缺少 token 或 `gh` 登录状态，请先让 Agent 配好再执行监控任务。
