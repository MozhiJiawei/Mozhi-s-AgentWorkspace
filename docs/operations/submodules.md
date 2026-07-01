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

## 更新 Skill

```powershell
git -C skills/<source-or-skill-name> pull
git add skills/<source-or-skill-name>
```

更新后，应复核文档或运行依赖是否发生变化。

## 变更后复核

```powershell
python loops/material-quality-guardian/qa/check_skill_docs.py
python loops/material-quality-guardian/qa/check_skill_dependencies.py
python scripts/pre_commit_gate.py
```

如果依赖相关文件发生变化，确认依赖状态后刷新依赖复核指纹。
