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

## 变更后复核

```powershell
python scripts/check_skill_docs.py
python scripts/check_skill_dependencies.py
python scripts/check_codex_agents_config.py
python scripts/pre_commit_gate.py
```

如果依赖相关文件发生变化，确认依赖状态后刷新依赖复核指纹。
如果子仓 `.codex/agents/*.toml` 发生变化，先运行 `python scripts/check_codex_agents_config.py --update`，再重新运行统一门禁。
