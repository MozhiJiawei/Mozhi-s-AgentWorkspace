# 快速开始

使用这个 workspace 的正确方式，不是记住一组脚本命令，而是让 Agent Runtime 认识它，然后用自然语言把任务交给 Agent。

这个 workspace 会把 skills、文档、门禁和临时产物约定组织在一起，让 Agent 知道“有哪些能力可用”“什么时候该组合哪些能力”“产物应该放在哪里”。

## 1. 配置 Agent Runtime

### 1.1 Codex

Codex 当前是本 workspace 的主要运行入口。

推荐接入方式：

1. 克隆本仓库并初始化 skill submodules。

   ```powershell
   git clone https://github.com/MozhiJiawei/Mozhi-s-AgentWorkspace.git
   cd Mozhi-s-AgentWorkspace
   git submodule update --init --recursive
   ```

2. 在 Codex App 中选择“使用现有文件夹”。
3. 添加刚刚克隆的 `Mozhi-s-AgentWorkspace` 目录作为 workspace。
4. 进入 workspace 后，让 Codex 先阅读仓库约定，再开始具体任务。

Codex 会通过以下文件认识 workspace：

- `AGENTS.md`：workspace 级 agent 指令、skill 暴露规则和使用约束。
- `README.md`：面向人类读者的仓库入口。
- `skills/*/SKILL.md`：每个 skill 的能力说明和触发规则。
- `skills/*/docs.manifest.yml`：每个 skill 暴露给文档站的说明入口。

首次进入后，可以先这样问：

```text
请先阅读这个 workspace 的 README.md 和 AGENTS.md，告诉我当前有哪些 skills，以及它们分别适合什么场景。
```

### 1.2 OpenClaw

TBD

## 2. 依赖配置

首次使用某个 skill 前，不需要自己先研究怎么装依赖。更合理的方式是让 Agent 阅读对应 skill 的依赖说明，运行依赖检查，并根据检查结果把环境处理到可用。

如果你准备使用某个 skill，再这样问：

```text
我要使用 ppt-deep-search，请先阅读它的依赖说明，运行依赖检查；如果缺依赖，请直接帮我处理到可用。
```

各 skill 的依赖说明入口：

| Skill | 依赖说明 |
| --- | --- |
| `ppt-deep-search` | [依赖说明](/skills/ppt-deep-search/dependencies) |
| `hw-ppt-gen-html` | [依赖说明](/skills/hw-ppt-gen-html/dependencies) |
| `grobid-docling-pdf` | [依赖说明](/skills/grobid_pdf_skill/dependencies) |
| `gh-issue-comment-monitor` | [依赖说明](/skills/gh-issue-comment-monitor/dependencies) |
| `send-qq-email` | [依赖说明](/skills/send-qq-email/dependencies) |
| `[beta] generate-3plus1-diagrams` | [依赖说明](/skills/architecture_4-1/dependencies) |

## 3. 使用方式

使用时，不需要先决定“我要调哪个脚本”。你只需要描述想完成的任务，Agent 会根据场景判断要不要调用一个或多个 skills。

下面的示例按“典型场景、典型 Prompt、预期调用的 Skills、预期产物”组织。

### 3.1 PPT 生成（zero-shot）：PDF 论文

典型场景：你有一篇论文 PDF，希望根据输入材料直接生成中文技术汇报 HTML 演示文稿，不先进入深度研究流程。

Prompt 示例：

- `请解析这篇论文 PDF，输出结构化 XML 和图表图片索引，用于后续分析。`
- `请基于这份 Markdown 材料提炼故事线，生成一份华为红灰配色的 HTML 业务汇报 deck，并导出 PNG 做视觉检查。`

预期调用的 Skills：

- `grobid-docling-pdf`
- `hw-ppt-gen-html`

预期产物：

- 论文结构化 XML
- 图表图片索引
- HTML 演示文稿
- PNG 导出图片
- 视觉 QA 和规则检查结果

### 3.2 PPT 生成（zero-shot）：新闻

典型场景：你有新闻、网页或文字材料，希望根据输入内容直接生成 HTML 汇报演示文稿，不先进入深度研究流程。

Prompt 示例：

- `请基于这份 Markdown 材料提炼故事线，生成一份华为红灰配色的 HTML 业务汇报 deck，并导出 PNG 做视觉检查。`
- `请读取这个仓库的分析结果，生成一份华为风格 HTML 技术方案 slides，重点检查正文内容不要重叠或裁切。`

预期调用的 Skills：

- `hw-ppt-gen-html`

预期产物：

- HTML 演示文稿
- PNG 导出图片
- 视觉 QA 和规则检查结果
- 可直接复用的汇报材料

### 3.3 PPT 深度研究

典型场景：你不想马上生成 PPT，而是先把来源材料、技术理解、可用图表和证据边界审清楚。

Prompt 示例：

- `请对这篇论文做 PPT深度研究，先产出 source_understanding_review.html，不要直接生成 PPT。`
- `请基于这些材料进行 PPT深度研究，产出可审阅的 Source Understanding HTML、截图和视觉 QA。`

预期调用的 Skills：

- `grobid-docling-pdf`
- `ppt-deep-search`

预期产物：

- `review/source_understanding_review.html`
- `review/source-understanding-images/`
- `review/visual-qa.md`
- `baselines/015-source-understanding.md`
- `sources/**`

### 3.4 GitHub Issue 跟进

典型场景：你需要跟进某个 GitHub Issue，但不想每次重复读取完整讨论历史。

Prompt 示例：

- `请检查 MozhiJiawei/Mozhi-s-AgentWorkspace#3 有没有新的 issue 评论，只处理上次之后的新回复。`
- `请读取这个 GitHub Issue 的最新 5 条评论，并在处理完成后更新本地 checkpoint。`

预期调用的 Skills：

- `gh-issue-comment-monitor`

预期产物：

- 本轮新增评论
- updates 文件
- checkpoint 状态
- 对新回复的摘要或后续处理建议

### 3.5 QQ 邮箱发邮件

典型场景：你希望 Agent 帮你组织邮件内容，并通过 QQ 邮箱发送。

Prompt 示例：

- `请用 QQ 邮箱 SMTP dry-run 一封测试邮件，并把 .eml 快照写到 .tmp/send-qq-email/。`
- `请检查我的 QQ 邮箱 SMTP 环境变量是否齐全，不要真实发送邮件。`

预期调用的 Skills：

- `send-qq-email`

预期产物：

- `.eml` 邮件快照
- 发送结果
- SMTP 配置检查结果
- 邮件主题、正文和收件人记录

### 3.6 [beta] 架构分析与画图

典型场景：你希望 Agent 阅读一个代码仓库，梳理模块边界、运行路径，并生成可编辑架构图。

当前状态：Beta。这个能力还不成熟，建议暂时谨慎使用。

Prompt 示例：

- `请基于这个仓库生成 4+1 架构图，只需要逻辑视图和运行时视图，输出 draw.io 文件。`
- `请梳理当前仓库的模块边界和关键运行路径，并给我一套可编辑的 3+1 架构图。`

预期调用的 Skills：

- `[beta] generate-3plus1-diagrams`

预期产物：

- 逻辑视图
- 开发视图
- 运行时视图
- 用例视图
- draw.io 文件
- 导出预览和校验结果
