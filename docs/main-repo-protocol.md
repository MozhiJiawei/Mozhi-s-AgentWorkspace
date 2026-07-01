# Main Repository Protocol

本文档定义本工作区主仓的工程协议。它描述主仓如何接入、注册、验证和运行 `skills/` 下的 skill 子仓。

本文档不规定 skill 的内部实现方式，不重复定义 Skill 规范，也不规定 `SKILL.md` 的格式或内容结构。

## 目标

主仓协议用于保证：

- 主仓可以稳定发现、注册和调用 skill 子仓。
- Agent 运行 skill 时的临时产物有统一边界。
- skill 子仓的运行依赖可以被显式登记、复核和验证。
- 新增或更新 skill 子仓后，主仓有一致的验收门禁。

## 主仓职责

主仓负责管理 Agent 工作区的公共约束和接入状态。

主仓必须维护：

- `.gitmodules`：记录 `skills/` 下的 submodule 来源。
- `AGENTS.md`：记录已暴露 skill 的加载路径、触发条件和主仓侧使用约束。
- `README.md`：记录工作区说明、日常操作说明和 skill prompt 示例。
- `docs/skill-dependencies.yml`：作为 skill 运行依赖的唯一登记入口。
- `scripts/pre_commit_gate.py`：作为提交前统一门禁入口。
- `.tmp/`：作为 Agent 临时产物的唯一工作根目录。

主仓不应：

- 复制或重写 skill 子仓的核心实现逻辑。
- 把某个 skill 的运行时中间产物保存到正式仓库目录。
- 在未登记依赖和未运行门禁的情况下声明 skill 已稳定接入。
- 绕过 `python scripts/pre_commit_gate.py` 单独挑选检查项作为提交依据。

## 依赖登记协议

`docs/skill-dependencies.yml` 是主仓中 skill 运行依赖的唯一登记入口。

每个已接入 skill 必须登记：

- skill 名称。
- skill 路径。
- 依赖复核指纹 `dependency_review.source_fingerprint`。
- 复核时间 `reviewed_at`。
- 复核人 `reviewed_by`。
- 复核说明 `note`。
- Windows 运行依赖。
- macOS 运行依赖或待补状态。
- 依赖验证命令。
- 外部服务、浏览器、硬件或可选依赖。

主仓依赖指纹覆盖可能影响运行依赖的文件。当前覆盖范围由 `scripts/check_skill_dependencies.py` 定义，包括：

- `SKILL.md`
- `verify_dependencies.py`
- `requirements*.txt`
- `pyproject.toml`
- `environment*.yml`
- `environment*.yaml`
- `package.json`
- `scripts/**/*.py`
- `install*.ps1`
- `install*.sh`
- `install*.bat`

这些文件变化后，必须复核依赖并刷新指纹：

```powershell
python scripts/check_skill_dependencies.py --update-fingerprints
```

刷新指纹只表示依赖已经被复核，不表示可以跳过实际依赖验证。

## 临时产物协议

`.tmp/` 是本工作区内所有 Agent 临时产物的唯一工作根目录。

skill 运行时产生的以下内容必须写入 `.tmp/` 下：

- 中间稿。
- 运行日志。
- 调试文件。
- 导出预览。
- 阶段性 PPT、XML、draw.io、图片或其他生成文件。
- 校验结果。
- 可删除归档。

如果 skill 自身说明给出了相对临时目录规则，应将该规则解释为相对于主仓 `.tmp/` 的子路径规则。

示例：

```text
<skill-name>/<task-name>/
```

应解释为：

```text
.tmp/<skill-name>/<task-name>/
```

不得解释为：

```text
skills/<skill-source>/<skill-name>/<task-name>/
```

正式、可追踪、需要评审的仓库内容不应放在 `.tmp/`。如果用户明确要求将结果作为正式产物纳入版本控制，Agent 应把最终产物写入用户指定位置或合适的正式目录，并避免把中间产物一起提交。

## 主仓注册协议

新增 skill submodule 后，主仓必须同步更新：

- `.gitmodules`
- `AGENTS.md`
- `README.md` 的 Skill Prompt 示例
- `docs/skill-dependencies.yml`

`AGENTS.md` 应记录主仓调用该 skill 所需的信息，包括：

- 加载路径。
- skill 名称。
- 主要用途。
- 触发条件。
- 不触发条件。
- 主仓侧临时产物目录要求。
- 主仓侧交付前校验要求。

`README.md` 应提供可直接复用的 prompt 示例，帮助用户稳定触发该 skill。

## 新增 Skill 接入流程

新增 skill 时，应按以下顺序操作：

1. 将 skill 作为 submodule 添加到 `skills/<skill-source>`。
2. 确认子仓满足 [Skill Repository Protocol](skill-repo-protocol.md)。
3. 根据 skill 自身说明提取主仓注册所需的触发条件、产物路径和校验要求。
4. 更新 `AGENTS.md` 注册该 skill。
5. 更新 `README.md` 的 Skill Prompt 示例。
6. 更新 `docs/skill-dependencies.yml` 登记依赖。
7. 运行该 skill 的依赖验证命令。
8. 刷新依赖复核指纹。
9. 运行 `python scripts/pre_commit_gate.py`。

如果任一步失败，不应提交接入变更。

## 更新 Skill 子仓流程

更新已有 skill submodule 后，应按以下顺序复核：

1. 检查子仓变更是否涉及依赖、自检脚本、校验脚本或主仓注册信息。
2. 如果主仓触发条件或使用约束需要变化，更新 `AGENTS.md`。
3. 如果 prompt 示例不再准确，更新 `README.md`。
4. 如果依赖可能变化，更新 `docs/skill-dependencies.yml`。
5. 运行该 skill 的 `verify_dependencies.py`。
6. 刷新 `dependency_review.source_fingerprint`。
7. 运行 `python scripts/pre_commit_gate.py`。

如果依赖没有变化，也应刷新指纹并在 `note` 中说明已复核。

## 提交前要求

每次提交前必须运行：

```powershell
python scripts/pre_commit_gate.py
```

门禁失败时不得提交。应先修复失败项，再重新运行统一门禁。

## 验收标准

一个 skill 接入完成，至少应满足：

- `git submodule status` 能看到该 skill。
- `AGENTS.md` 中有对应注册项。
- `README.md` 中有对应 prompt 示例。
- `docs/skill-dependencies.yml` 中有对应依赖记录。
- 子仓满足 [Skill Repository Protocol](skill-repo-protocol.md)。
- 依赖复核指纹是最新的。
- `python scripts/pre_commit_gate.py` 通过。

只有满足以上条件，主仓才应把该 skill 视为已稳定接入。
