# Submodules

Skills 挂载在 `skills/` 下，默认使用 Git submodule 管理。

## 初始化

```powershell
git submodule update --init --recursive
```

## 添加 Skill

```powershell
git submodule add <repo-url> skills/<source-or-skill-name>
```

随后在主仓中注册这个 skill，让人类读者和 agent 都能发现它：

- `AGENTS.md`
- `README.md` 的 Skill Prompt 示例
- `docs/skill-docs.yml`
- `docs/skill-dependencies.yml`

如果子仓提供 Codex 原生子 agent 定义，还需要刷新根配置：

```powershell
python scripts/check_codex_agents_config.py --update
```

## 更新 Skill

```powershell
git -C skills/<source-or-skill-name> pull
git add skills/<source-or-skill-name>
```

更新后，应复核文档或运行依赖是否发生变化。

完整接入与更新步骤见 [主仓协议](/main-repo-protocol)。

## 变更后复核

```powershell
python scripts/sync_skill_docs.py
python scripts/check_skill_docs.py
python scripts/check_skill_dependencies.py
python scripts/check_codex_agents_config.py
python scripts/pre_commit_gate.py
```

运行上述检查前，应阅读并运行目标 skill 的依赖自检。文档相关文件发生变化时，复核资料后使用 `python scripts/check_skill_docs.py --update-fingerprints` 刷新文档复核指纹；依赖相关文件发生变化时，确认依赖状态后使用 `python scripts/check_skill_dependencies.py --update-fingerprints` 刷新依赖复核指纹。
如果子仓 `.codex/agents/*.toml` 发生变化，先运行 `python scripts/check_codex_agents_config.py --update`，再重新运行统一门禁。
