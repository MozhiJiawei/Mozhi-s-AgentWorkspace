---
layout: home

hero:
  name: Mozhi's Agent Workspace
  text: "从偶现的 AI 灵光一闪，\n到稳定的 Agent 生产力。"
  tagline: 可复用的 Agent skills 工作区，用来沉淀高质量技术规划、软件开发和日常工作技能。
  actions:
    - theme: brand
      text: 快速开始
      link: /workspace/getting-started
    - theme: alt
      text: Skills
      link: /skills/
    - theme: alt
      text: 核心概念
      link: /workspace/concepts

features:
  - title: 贴合工作场景
    details: 面向真实产出深度定制 PPT 风格、论文推荐算法和日常流程，让 Agent 交付更贴近工作现场、可以直接复用。
  - title: 编排与技能分离
    details: Workspace 负责编排、文档和门禁；Skill 仓库保持独立开发，按统一 manifest、依赖复核和文档规范持续演进。
  - title: Runtime 无关
    details: 不绑定单一 Agent Runtime，Skill 能力以通用约定沉淀；当前暂仅支持 Codex，计划适配 OpenClaw 等主流运行环境。
---

## 当前支持的 Skills

| Skill | 能力 |
| --- | --- |
| [ppt-deep-search](/skills/ppt-deep-search/) | 在生成 PPT 前完成深度研究、观点对齐、故事线规划和证据审计。 |
| [hw-ppt-gen-html](/skills/hw-ppt-gen-html/) | 基于材料生成 HTML PPT / slides，并完成 PNG 导出和独立视觉 QA。 |
| [gh-issue-comment-monitor](/skills/gh-issue-comment-monitor/) | 增量读取 GitHub Issue 新评论，避免重复加载完整讨论历史。 |
| [grobid-docling-pdf](/skills/grobid_pdf_skill/) | 解析论文或技术 PDF，输出结构化 XML、图表图片和可追踪中间结果。 |
| [send-qq-email](/skills/send-qq-email/) | 通过 QQ 邮箱 SMTP dry-run 或发送邮件，并生成 `.eml` 快照。 |
| [web-article-capture](/skills/web-article-capture/) | 抓取网页正文文本和原始正文图片，生成下游可复用的 source package。 |
| [[beta] generate-3plus1-diagrams](/skills/architecture_4-1/) | 分析代码仓库架构，生成 3+1 / 4+1 架构视图和可编辑 draw.io 图。 |

更多细节见 [Skills](/skills/)。
