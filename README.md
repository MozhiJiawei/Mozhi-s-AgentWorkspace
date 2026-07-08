# Mozhi's Agent Workspace

<p align="center">
  <strong>从偶现的 AI 灵光一闪，<br>到稳定的 Agent 生产力。</strong>
</p>

<p align="center">
  <a href="http://docs.haohaoxiaoyu.top:8888/">文档站</a>
  ·
  <a href="./docs/workspace/getting-started.md">快速开始</a>
  ·
  <a href="#已注册-skills">Skills</a>
  ·
  <a href="./docs/workspace/concepts.md">核心概念</a>
</p>

<p align="center">
  <img alt="docs" src="https://img.shields.io/badge/docs-VitePress-2ea44f">
  <img alt="skills" src="https://img.shields.io/badge/skills-submodules-blue">
  <img alt="gate" src="https://img.shields.io/badge/gate-pre--commit-orange">
  <img alt="workspace" src="https://img.shields.io/badge/workspace-agent--ready-24292f">
</p>

可复用的 Agent skills 工作区，用来沉淀高质量技术规划、软件开发和日常工作技能。

Mozhi's Agent Workspace 面向真实工作中的 Agent 生产力沉淀：把 PPT 来源理解审阅、HTML 演示文稿生成、论文 PDF 解析、Issue 跟进、邮件发送和架构画图等 skills 组织到同一个可维护、可发布、可校验的工作区里。

| 架构目标 | 说明 |
| --- | --- |
| 贴合工作场景 | 面向真实产出深度定制 PPT 风格、论文推荐算法和日常流程，让 Agent 交付更贴近工作现场、可以直接复用。 |
| 编排与技能分离 | Workspace 负责编排、文档和门禁；Skill 仓库保持独立开发，按统一 manifest、依赖复核和文档规范持续演进。 |
| Runtime 无关 | 不绑定单一 Agent Runtime，Skill 能力以通用约定沉淀；当前暂仅支持 Codex，计划适配 OpenClaw 等主流运行环境。 |

## 从这里开始

| 我想要... | 入口 |
| --- | --- |
| 使用已有 skill | [已注册 Skills](#已注册-skills) |
| 理解工作区模型 | [核心概念](./docs/workspace/concepts.md) |
| 运行文档站 | [文档服务器](./docs/operations/docs-server.md) |
| 接入或维护 skill | [Skill 子仓协议](./docs/reference/skill-repo-protocol.md) |
| 检查仓库健康状态 | [Pre-Commit Gates](./docs/operations/pre-commit-gates.md) |

## 快速开始

```powershell
git submodule update --init --recursive
npm install
npm run docs:dev
python scripts/pre_commit_gate.py
```

本地文档站地址：

```text
http://127.0.0.1:5173/
```

## 仓库结构

```text
.
|-- AGENTS.md          # agent 可读的 skill 注册表和使用约束
|-- README.md          # 面向人类读者的 GitHub 入口
|-- .codex/            # Codex 原生子 agent 的主仓级配置
|-- docs/              # 主仓文档和统一文档站
|-- skills/            # skill 子仓；每个 skill 拥有自己的文档
|-- scripts/           # 主仓检查脚本和文档编排脚本
`-- .tmp/              # 运行时产物、草稿、日志和导出文件
```

## 文档模型

这个工作区遵循一条边界：

```text
主仓负责：
- 工作区协议
- 文档服务器
- Skills
- 依赖与文档门禁

Skill 子仓负责：
- 使用说明
- 示例
- 限制
- 排障
- 依赖验证
```

统一文档站把这些内容聚合到同一个发布面里，但不会让主仓变成每个 skill 正文的权威来源。

## 已注册 Skills

完整索引由文档服务器从各 skill 子仓生成；当前已接入的 skill 包括：

| Skill | 用途 |
| --- | --- |
| `ppt-deep-search` | 在生成 PPT 前完成来源理解审阅、证据边界确认和 Source Understanding HTML。 |
| `web-article-capture` | 抓取网页正文文本和原始正文图片，生成下游可复用的 source package。 |
| `hw-ppt-gen-html` | 生成浏览器可打开的 HTML PPT / slides，并完成 PNG 导出和独立视觉 QA。 |
| `grobid-docling-pdf` | 将论文或技术 PDF 解析成结构化 XML 和图表图片。 |
| `gh-issue-comment-monitor` | 增量监控 GitHub Issue 评论。 |
| `send-qq-email` | 通过 QQ 邮箱 SMTP 发送或 dry-run 邮件，并生成快照。 |
| `[beta] generate-3plus1-diagrams` | 生成 3+1 / 4+1 架构视图和 draw.io 图。 |

## Skill Prompt 示例

下面这些 prompt 可以作为快速入口。完整说明仍以各 skill 子仓自己的文档为准。

### `skills/gh-issue-comment-monitor`

- `请检查 MozhiJiawei/Mozhi-s-AgentWorkspace#3 有没有新的 issue 评论，只处理上次之后的新回复。`
- `请读取这个 GitHub Issue 的最新 5 条评论，并在处理完成后更新本地 checkpoint。`

### `skills/hw-ppt-gen-html`

- `请基于这份 Markdown 材料提炼故事线，生成一份华为红灰配色的 HTML 业务汇报 deck，并导出 PNG 做视觉检查。`
- `请用 HTML/CSS 做一份技术汇报 slides，交付 index.html、导出图片和 visual-qa.md。`

### `skills/ppt-deep-search`

- `请对这篇论文做 PPT深度研究，先产出 source_understanding_review.html，不要直接生成 PPT。`
- `请基于这些材料进行 PPT深度研究，产出可审阅的 source_understanding_review.html。`

### `skills/web-article-capture`

- `请使用 web-article-capture 抓取这些网页的正文和正文图片，把 source package 写到 .tmp/web-article-capture/<任务名>/。`
- `请把这篇官方博客渲染后的正文、图表和原始图片链接整理成 source.md，并运行 validate_capture_package.py 校验。`

### `skills/grobid_pdf_skill`

- `请解析这篇论文 PDF，输出结构化 XML 和图表图片索引，用于后续分析。`
- `请把这篇论文 PDF 的正文、引用、参考文献、图和表整理成 agent 可消费的结构化结果。`

### `skills/send-qq-email`

- `请用 QQ 邮箱 SMTP dry-run 一封测试邮件，并把 .eml 快照写到 .tmp/send-qq-email/。`
- `请检查我的 QQ 邮箱 SMTP 环境变量是否齐全，不要真实发送邮件。`

### `[beta] skills/architecture_4-1`

- `请基于这个仓库生成 4+1 架构图，只需要逻辑视图和运行时视图，输出 draw.io 文件。`
- `请梳理当前仓库的模块边界和关键运行路径，并给我一套可编辑的 3+1 架构图。`

## 维护

修改 skill 资料前，先阅读 [文档架构需求](./docs/documentation-architecture-requirements.md)。其中的 `Skill 资料页面要求` 定义 `能力展示`、`使用方式`、`依赖说明`、`架构概览` 四个必选页面的写作要求，也是 Agent 补写或审查资料时的参考入口。

提交仓库改动前，运行统一门禁：

```powershell
python scripts/pre_commit_gate.py
```

该入口会编排文档漂移检查、skill 依赖复核检查、注册表检查和 README prompt 示例覆盖检查。准备提交时不要绕过它单独挑选检查项。

接入带 Codex 原生子 agent 的 skill 时，先运行 `python scripts/check_codex_agents_config.py --update`，由脚本把子仓 `.codex/agents/*.toml` 同步到主仓 `.codex/config.toml`，再运行统一门禁。

## 原则

- Skill 文档留在对应 skill 子仓。
- 主仓文档只解释工作区级协议和入口。
- 运行时产物写入 `.tmp/`。
- 文档站是统一发布面，不是第二份正文来源。
- 每次提交前都应通过统一 pre-commit gate。
