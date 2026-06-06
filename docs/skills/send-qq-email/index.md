# QQ 邮件发送

`send-qq-email` 是一个轻量 SMTP skill，用来通过 QQ 邮箱发送 UTF-8 文本 / HTML 邮件，或在不真实发送的情况下生成 `.eml` 快照和结构化结果。

## 架构概览

这个 skill 的核心是一个独立发送脚本：

| 模块 | 职责 |
| --- | --- |
| `SKILL.md` | 定义触发场景、真实发送确认规则、缺失配置时的用户指引。 |
| `scripts/send_qq_email.py` | 读取 SMTP 配置，构造 MIME 邮件，执行 dry-run 或真实发送，并输出 JSON 结果。 |
| `references/smtp-config.md` | 保存 QQ 邮箱授权码、环境变量和私有配置文件说明。 |
| `verify_dependencies.py` | 编译脚本并使用临时假配置执行 dry-run smoke test。 |

## 数据流

```text
Prompt / message content
  -> SMTP config from env or private config file
  -> MIME message
  -> message.eml
  -> dry_run result or SMTP send result
  -> result.json
```

## 配置来源

脚本按以下方式读取 SMTP 配置：

1. 显式 `--config` 文件。
2. `SEND_QQ_EMAIL_CONFIG` 指向的私有配置文件。
3. 默认私有配置：`~/.send-qq-email/email.yaml`。
4. 环境变量覆盖配置文件字段。

真实凭据不应写入仓库。QQ 邮箱 SMTP 使用授权码作为 `SMTP_PASSWORD`，不是 QQ 登录密码。

## 设计边界

- 配置检查、预览和验证默认使用 dry-run。
- 真实发送前，如果收件人或意图不明确，Agent 应先确认。
- 脚本可以写 `.eml` 和 `result.json`，但不记录 SMTP 密码或授权码。
- 输出目录在主工作区中应放到 `.tmp/send-qq-email/` 下。

## 输出契约

脚本会在输出目录写入：

```text
.tmp/send-qq-email/<task>/
|-- message.eml
`-- result.json
```

`result.json` 用固定字段表达发送状态，包括 `status`、`recipient`、`sent_at`、`error_type`、`error_summary`、`message_id`、`eml_path` 和 `dry_run`。

真实发送失败时也会保留 `.eml`，方便复核邮件内容是否正确。

## 子仓文档导航

- [能力展示](./reference.md)
- [使用方式](./usage.md)
- [依赖说明](./dependencies.md)
- [架构概览](./)
