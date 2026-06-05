# 工作区概览

Mozhi's Agent Workspace 是用于协调 Codex skills 的主仓。各个 skill 以独立子仓形式挂载在 `skills/` 下。

这个工作区不是为了把每个 skill 的说明都搬进主仓，而是提供一套共享结构，让这些 skill 可以被发现、被复核、被发布，并通过同一个文档站呈现给读者。

## 工作区负责什么

- 注册 skill 及其 agent-facing 使用约束。
- 发布统一的 VitePress 文档站。
- 检查 skill 文档 manifest 是否漂移。
- 追踪 skill 依赖复核指纹。
- 提供统一的提交前健康门禁。
- 约定 `.tmp/` 作为运行时产物根目录。

## Skill 子仓负责什么

每个 skill 子仓拥有自己的内容和行为：

- `SKILL.md`
- `docs.manifest.yml`
- `docs/index.md`
- `docs/usage.md`
- `docs/reference.md`
- `verify_dependencies.py`
- 示例、脚本、参考资料、测试和排障材料

工作区可以总结和路由到某个 skill，但 skill 自身仍然是其使用说明的权威来源。

## 仓库角色

| 区域 | 所属方 | 用途 |
| --- | --- | --- |
| `README.md` | 主仓 | GitHub 入口和人类读者导览 |
| `AGENTS.md` | 主仓 | Agent 可读的 skill 注册表和使用约束 |
| `docs/` | 主仓 | 工作区文档和统一发布面 |
| `skills/*` | Skill 子仓 | Skill 行为、文档、依赖和验证 |
| `.tmp/` | 运行时 | 草稿、日志、导出物和中间产物 |
| `scripts/` | 主仓 | 工作区检查和文档编排 |

## 下一步

- 第一次进入仓库：阅读 [快速开始](./getting-started)。
- 建立心智模型：阅读 [核心概念](./concepts)。
- 运行文档站：阅读 [文档服务器](/operations/docs-server)。
- 维护检查项：阅读 [Pre-Commit Gates](/operations/pre-commit-gates)。
