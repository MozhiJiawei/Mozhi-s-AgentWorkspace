# 主仓协议

本页是主仓工程协议的对外 reference 版本。完整说明见 [`docs/main-repo-protocol.md`](/main-repo-protocol)。

## 适用范围

主仓协议定义 Agent 工作区主仓如何接入、注册、验证和运行 `skills/` 下的 skill 子仓。

它不规定 skill 的内部实现方式，不重复定义 Skill 规范，也不规定 `SKILL.md` 的格式或内容结构。

## 主仓职责

主仓必须维护以下稳定入口：

| 入口 | 职责 |
| --- | --- |
| `.gitmodules` | 记录 `skills/` 下的 submodule 来源。 |
| `AGENTS.md` | 记录已暴露 skill 的加载路径、触发条件和主仓侧使用约束。 |
| `README.md` | 记录工作区说明、日常操作说明和 skill prompt 示例。 |
| `.codex/config.toml` | 登记 Codex 原生子 agent 的主仓级入口。 |
| `docs/skill-dependencies.yml` | 登记 skill 运行依赖与复核指纹。 |
| `docs/skill-docs.yml` | 登记 skill 文档发布来源与复核指纹。 |
| `scripts/pre_commit_gate.py` | 提交前统一门禁入口。 |
| `.tmp/` | Agent 临时产物唯一工作根目录。 |

主仓不应复制 skill 子仓的核心实现逻辑，不应把运行时中间产物写入正式仓库目录，也不应绕过统一门禁声明接入完成。

## 临时产物协议

`.tmp/` 是本工作区内所有 Agent 临时产物的唯一工作根目录。

以下内容必须写入 `.tmp/` 下：

- 中间稿、运行日志、调试文件。
- 导出预览、阶段性 PPT、XML、draw.io、图片或其他生成文件。
- 校验结果和可删除归档。

如果 skill 自身说明给出了相对临时目录规则，应解释为 `.tmp/` 的子路径。例如 `<skill-name>/<task-name>/` 应落到 `.tmp/<skill-name>/<task-name>/`。

## Skill 接入流程

新增 skill 时应按顺序完成：

1. 将 skill 作为 submodule 添加到 `skills/<skill-source>`。
2. 确认子仓满足 [Skill 子仓协议](./skill-repo-protocol)。
3. 更新 `AGENTS.md`、`README.md`、`docs/skill-dependencies.yml` 和 `docs/skill-docs.yml`。
4. 如果子仓提供 `.codex/agents/*.toml`，运行 `python scripts/check_codex_agents_config.py --update` 刷新 `.codex/config.toml`。
5. 运行 skill 的依赖验证命令。
6. 刷新依赖和文档复核指纹。
7. 运行 `python scripts/pre_commit_gate.py`。

任一步失败时，不应提交接入变更。

## 提交前要求

每次提交前必须运行：

```powershell
python scripts/pre_commit_gate.py
```

门禁失败时不得提交。应先修复失败项，再重新运行统一门禁。
