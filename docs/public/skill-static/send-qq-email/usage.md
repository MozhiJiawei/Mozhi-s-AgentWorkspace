# 使用方式

这个 skill 面向 Agent 原生工作流：你描述要发什么、发给谁、是否只是预览，Agent 负责检查配置、生成邮件快照和执行发送。

## 典型 Prompt

- `请用 QQ 邮箱 SMTP dry-run 一封测试邮件，并把 .eml 快照写到 .tmp/send-qq-email/。`
- `请检查我的 QQ 邮箱 SMTP 环境变量是否齐全，不要真实发送邮件。`
- `请把这段日报内容通过 QQ 邮箱发给我指定的收件人；发送前先确认收件人。`

## 推荐流程

1. 明确这是 dry-run、配置检查，还是真实发送。
2. 真实发送前确认收件人和发送意图。
3. 从环境变量或私有配置文件读取 SMTP 设置。
4. 构造 UTF-8 MIME 邮件。
5. 写入 `.eml` 快照和 `result.json`。
6. dry-run 到此结束；真实发送则继续连接 `smtp.qq.com`。

## 必要配置

| 字段 | 说明 |
| --- | --- |
| `SMTP_USERNAME` | QQ 邮箱地址。 |
| `SMTP_PASSWORD` | QQ 邮箱 SMTP 授权码，不是登录密码。 |
| `SMTP_TO` | 默认收件人，也可用 `--to` 覆盖。 |

更多配置字段见子仓 `references/smtp-config.md`。

## 脚本入口

dry-run 测试邮件：

```powershell
python scripts/send_qq_email.py `
  --test `
  --dry-run `
  --output-dir .tmp/send-qq-email/test
```

发送自定义正文：

```powershell
python scripts/send_qq_email.py `
  --subject "Daily report" `
  --text-file report.txt `
  --to receiver@example.com `
  --output-dir .tmp/send-qq-email/daily-report
```

使用私有配置文件：

```powershell
python scripts/send_qq_email.py `
  --config "$env:USERPROFILE\.send-qq-email\email.yaml" `
  --test `
  --dry-run `
  --output-dir .tmp/send-qq-email/config-check
```

## 依赖检查

```powershell
python verify_dependencies.py
```

该检查只执行 dry-run smoke test，不会真实发送邮件。
