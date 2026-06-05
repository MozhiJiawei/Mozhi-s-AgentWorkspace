# Pre-Commit Gates

仓库提交前使用一个统一门禁入口：

```powershell
python scripts/pre_commit_gate.py
```

准备提交时，不要用手动挑选的检查项替代这个入口。

## 门禁保护什么

门禁用于保持工作区在以下方面一致：

- `AGENTS.md` 中的 skill 注册
- skill 文档 manifest 和源文件指纹
- skill 依赖复核指纹
- README 中的 skill prompt 示例覆盖
- 仓库级文档约定

## 失败时怎么办

把失败视为漂移信号。先修复底层问题，再重新运行统一门禁。

常见情况：

| 信号 | 通常处理方式 |
| --- | --- |
| Skill 文档变化 | 复核 docs manifest，并在需要时刷新文档指纹。 |
| 依赖相关文件变化 | 复核运行依赖，并刷新依赖指纹。 |
| 注册表不一致 | 更新对应注册表条目。 |
| README prompt 覆盖失败 | 补充或更新对应 prompt 示例。 |

## 提交规则

只要任一门禁失败，就不要提交。先修复失败项。
