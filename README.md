# Mozhi's Agent Workspace

这是一个为 Codex agent 设计的工作区骨架，用来集中维护仓库说明、skills 子仓，以及 skills 运行时生成的临时产物。

## 目录结构

```text
.
|-- AGENTS.md
|-- README.md
|-- .gitignore
|-- .tmp/
|   `-- .gitkeep
+-- skills/
    `-- .gitkeep
```

## 仓库约定

- `README.md` 保存仓库说明、目录职责和工程约定。
- 当 agent 需要修改仓库代码、调整目录结构或处理非 skill 内容时，应先阅读 `README.md`。
- `AGENTS.md` 只保存 skills 的暴露说明和使用约束。
- `skills/` 只用于挂载 skill 来源仓，默认采用多个 Git submodule 的组织方式。
- `.tmp/` 用于存放 skill 运行时生成的草稿、日志、调试文件和导出物；这些内容默认不进入版本控制。

## 添加一个 skill submodule

在仓库根目录执行：

```powershell
git submodule add <repo-url> skills/<source-or-skill-name>
git commit -m "Add skill submodule: <source-or-skill-name>"
```

命名建议：

- 目录名使用 skill 来源名或 skill 包名
- 尽量稳定，不随单次任务改名
- 一个来源一个目录，避免把多个无关来源混在同一个子模块路径下

## 更新与同步 submodule

拉取仓库后初始化并同步子模块：

```powershell
git submodule update --init --recursive
```

更新某个已接入 skill：

```powershell
git -C skills/<source-or-skill-name> pull
git add skills/<source-or-skill-name>
git commit -m "Update skill submodule: <source-or-skill-name>"
```

## Skill 依赖管理

`docs/skill-dependencies.yml` 是 skill 运行依赖的唯一登记入口。每个 skill 都应在其中登记：

- skill 路径
- 依赖复核指纹
- Windows 运行依赖
- macOS 运行依赖或待补状态
- 验证命令

每个 skill 子仓根目录必须提供统一入口：

```powershell
python verify_dependencies.py
```

该脚本应兼容 Windows 和 macOS，并由 skill 自己验证运行所需的 Python 包、浏览器运行时、外部服务或可选硬件能力。仓库级门禁会检查这个脚本是否存在，并把它纳入依赖复核指纹。

依赖复核指纹只覆盖可能影响运行依赖的文件，例如 `SKILL.md`、`verify_dependencies.py`、`requirements*.txt`、`pyproject.toml`、`environment*.yml`、`package.json`、`scripts/**/*.py` 和安装脚本。

新增 skill 或更新 skill submodule 后，应先复核依赖是否变化：

- 若依赖变化，更新 `docs/skill-dependencies.yml` 中对应平台的依赖条目。
- 若依赖没有变化，也要刷新 `dependency_review.source_fingerprint`，并在 `note` 中说明已复核。

刷新指纹：

```powershell
python scripts/check_skill_dependencies.py --update-fingerprints
```

提交前统一门禁会运行：

```powershell
python scripts/pre_commit_gate.py
```

如果 skill 的依赖相关文件变化但依赖清单没有复核，门禁会失败并提示刷新依赖登记。

## .tmp/ 使用方式

当 prompt 引导某个 skill 工作时，生成产物应默认写到：

- `.tmp/<skill-name>/`
- `.tmp/<date-task>/`

推荐把这类内容放进 `.tmp/`：

- 中间结果
- 导出文件
- 调试日志
- 草稿与实验性产物

不建议把需要长期保留、需要评审或需要版本追踪的正式内容放进 `.tmp/`。

## Skill Prompt 示例

本节为每个已注册 skill 提供几条可直接复用的 prompt 示例，便于快速触发对应能力。

### `skills/gh-issue-comment-monitor`

适用场景：监控 GitHub Issue 评论增量，只读取最新回复或 checkpoint 之后的新评论，避免重复加载完整 issue 历史。

示例 prompt：

- `请检查 MozhiJiawei/Mozhi-s-AgentWorkspace#3 有没有新的 issue 评论，只处理上次之后的新回复。`
- `请读取这个 GitHub Issue 的最新 5 条评论，并在处理完成后更新本地 checkpoint。`
- `请监控这个 issue 的评论更新，把本轮 updates 文件放到 .tmp/gh-issue-comment-monitor/。`

### `skills/architecture_4-1`

适用场景：分析目标仓库架构，产出 3+1 / 4+1 架构视图、draw.io 图和相关校验结果。

示例 prompt：

- `请你分析目标仓库里的 omni_infer 模块，给出 omniProxy 的用例视图，重点突出加速特性。允许参照SKILL描述使用子agent配合分析。`
- `请基于这个仓库生成 4+1 架构图，只需要逻辑视图和运行时视图，输出 draw.io 文件。允许参照SKILL描述使用子agent配合分析。`
- `请梳理当前仓库的模块边界和关键运行路径，并给我一套可编辑的 3+1 架构图。允许参照SKILL描述使用子agent配合分析。`

### `skills/hw-ppt-gen`

适用场景：基于网页、Markdown、论文解析结果、仓库分析、纯文本或用户 prompt，生成华为风格的新 PPTX，并在交付前执行参考图审阅、硬规则 QA、导出图片和视觉 QA。

示例 prompt：

- `请根据这篇论文 PDF 的解析结果生成一份 12 页左右的华为风格技术汇报 PPTX，正文使用中文。`
- `请基于这份 Markdown 材料提炼故事线，生成一份华为红灰配色的业务汇报 deck，并导出图片做视觉检查。`
- `请读取这个仓库的分析结果，生成一份华为风格技术方案 PPTX，重点检查章节指示器、分析总结块和正文内容不要重叠或裁切。`

### `skills/ppt-deep-search`

适用场景：只有当 prompt 明确出现“PPT深度研究”时，才在生成 PPT 前先做人机协同的观点对齐、故事线规划和证据审计，输出可交给 PPT 生成 skill 的 `ppt_content_brief.md` 与 `research_audit.md`。普通 PPT 制作需求仍直接使用 `skills/hw-ppt-gen`。

示例 prompt：

- `请对这篇论文做 PPT深度研究，先帮我确定读者、核心观点和页面故事线，不要直接生成 PPT。`
- `请基于这些材料进行 PPT深度研究，产出通过校验的 ppt_content_brief.md 和 research_audit.md，后续再交给 PPT 生成流程。`
- `请先用 PPT深度研究 对齐这份技术汇报的证据边界和页面标题，再进入华为风格 PPT 生成。`

### `skills/grobid_pdf_skill`

适用场景：解析论文或技术 PDF，使用 GROBID 提取学术文本结构与参考文献，使用 Docling 导出图表图片，并生成一个可供后续 agent 理解和引用的 TEI/XML 包。

示例 prompt：

- `请解析这篇论文 PDF，输出结构化 XML 和图表图片索引，用于后续分析。`
- `请先用 PDF 解析 skill 读取这篇论文，再基于解析结果总结方法、实验和结论。`
- `请把这篇论文 PDF 的正文、引用、参考文献、图和表整理成 agent 可消费的结构化结果。`

### `skills/send-qq-email`

适用场景：通过 QQ 邮箱 SMTP 发送或 dry-run 测试邮件，验证 SMTP 配置，生成 `.eml` 快照和结构化发送结果。

示例 prompt：

- `请用 QQ 邮箱 SMTP dry-run 一封测试邮件，并把 .eml 快照写到 .tmp/send-qq-email/。`
- `请检查我的 QQ 邮箱 SMTP 环境变量是否齐全，不要真实发送邮件。`
- `请用已配置的 QQ 邮箱授权码给 receiver@example.com 发送一封 HTML 测试邮件。`
