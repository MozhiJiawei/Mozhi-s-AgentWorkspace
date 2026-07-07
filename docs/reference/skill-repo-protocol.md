# Skill 子仓协议

本页定义接入本工作区的 skill 子仓需要满足的稳定工程要求。完整说明见 [`docs/skill-repo-protocol.md`](/skill-repo-protocol)。

## 适用范围

子仓协议用于保证：

- 主仓可以验证 skill 的运行依赖。
- Agent 可以通过脚本化入口判断 skill 是否可用。
- skill 生成的可检查产物有明确校验方式。
- skill 子仓不依赖未声明的本机环境。

本协议不规定 skill 的内部实现方式，也不重复定义 `SKILL.md` 的内容结构。

## 依赖自检入口

每个 skill 子仓根目录必须提供：

```powershell
python verify_dependencies.py
```

该脚本是主仓判断 skill 运行环境是否可用的统一入口。

脚本应满足：

| 要求 | 说明 |
| --- | --- |
| 必需依赖检查 | 对 Python 包、系统工具、浏览器运行时或外部服务等必需依赖缺失返回非零退出码。 |
| 可选依赖说明 | 对可选能力缺失给出警告，不应误报为必然失败。 |
| Windows 可运行 | 当前主仓以 Windows Agent 工作流为主要运行环境。 |
| 输出可操作 | 输出应说明缺失项和修复方向。 |

如果 skill 依赖外部服务，建议提供跳过服务检查的参数，例如 `--skip-services`。

## 校验脚本要求

如果 skill 生成可检查的最终产物，子仓应提供脚本化校验入口。校验脚本不要求统一命名，但必须能在 `SKILL.md` 或主仓注册说明中明确找到。

校验脚本应：

- 能从主仓根目录稳定调用。
- 通过命令行参数接收输入文件或输出目录。
- 对校验失败返回非零退出码。
- 输出具体失败原因。
- 不要求 Agent 手工打开 IDE 或图形界面才能判断是否通过。

## Codex 原生子 Agent

如果 skill 子仓提供 Codex 原生子 agent，应把稳定定义放在 `.codex/agents/*.toml`。

每个 agent TOML 必须包含 `name`、`description` 和 `developer_instructions`。`name` 必须在整个工作区内唯一。

主仓会通过 `scripts/check_codex_agents_config.py` 扫描这些定义，并要求根目录 `.codex/config.toml` 中存在一致的 `[agents.<name>]` 登记。主仓只登记描述和 `config_file` 引用，不复制子仓的 `developer_instructions` 正文。

## 临时产物边界

skill 子仓不应要求把运行时中间产物写回子仓自身目录。

如果 skill 需要临时目录，应把目录规则设计为可挂载到主仓 `.tmp/` 下。正式产物是否进入主仓正式目录，由用户请求和主仓约定决定。

## 接入验收

一个 skill 子仓可被主仓接入，至少应满足：

- 子仓根目录存在 `verify_dependencies.py`。
- `python verify_dependencies.py` 能在 Windows Agent 工作流中运行。
- 必需依赖缺失时返回非零退出码。
- 可选依赖缺失时给出明确警告。
- 若存在可检查最终产物，提供脚本化校验入口。
- 若提供 `.codex/agents/*.toml`，agent TOML 字段完整、名称唯一，并可被主仓 `.codex/config.toml` 引用。
- 不要求临时产物写入 skill 子仓。
- 不依赖未声明的外部环境。
