# 贡献指南

感谢你帮助改进 Mozhi's Agent Workspace。

## 先读这些文档

- 工作区模型：`docs/workspace/concepts.md`
- Skill 子仓规则：`docs/reference/skill-repo-protocol.md`
- 文档 manifest 规则：`docs/reference/skill-docs-manifest.md`
- 门禁说明：`docs/operations/pre-commit-gates.md`

## 仓库边界

- 主仓级文档写在 `docs/`。
- Skill 专属文档写在对应 `skills/<skill>/docs/`。
- 临时产物写在 `.tmp/`。
- Agent-facing 的 skill 暴露规则写在 `AGENTS.md`。

## 提交前

运行：

```powershell
python scripts/pre_commit_gate.py
```

如果门禁失败，先修复报告中的漂移或校验问题，再提交。

## 添加或更新 Skills

添加或更新 skill submodule 时，复核：

- `AGENTS.md`
- `docs/skill-docs.yml`
- `docs/skill-dependencies.yml`
- skill 的 `docs.manifest.yml`
- skill 的 `verify_dependencies.py`

Skill 自己的使用说明应保留在 skill 子仓中。
