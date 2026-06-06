# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 send-qq-email，请先检查邮件发送依赖；如果 QQ 邮箱 SMTP 凭据或网络前置条件没有准备好，请提示我补齐。
```

## 检查命令

在 workspace 根目录运行：

```powershell
python skills/send-qq-email/verify_dependencies.py
```

## 它会检查什么

| 类型 | 说明 |
| --- | --- |
| Python 脚本 | 检查邮件发送脚本是否能正常编译 |
| dry-run | 使用临时假配置生成 `.eml` 快照，确认本地流程可用 |
| SMTP 凭据 | 真实发送前需要 QQ 邮箱 SMTP 授权码和收件人配置 |
| 网络 | 真实发送时需要访问 `smtp.qq.com:587` |

## 判断标准

依赖检查通过表示本地生成和 dry-run 流程可用。真实发送前，还需要让 Agent 确认 SMTP 用户名、授权码、收件人和发送意图。
