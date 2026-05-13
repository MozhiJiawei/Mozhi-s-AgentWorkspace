# AGENTS.md

本文件只保存 skills 的暴露说明和使用约束，不保存仓库说明。

当任务涉及修改仓库代码、调整目录结构、更新工程约定或处理非 skill 内容时，agent 应先阅读 `README.md`。

## `.tmp/` Usage Principle

- `.tmp/` 是 agent 在本工作区内处理所有临时产物时唯一的工作根目录。
- 调用任何 skill 时产生的中间稿、日志、草图、导出文件和阶段性结果，都必须写入 `.tmp/` 下。
- 具体子目录命名和拼接方式，按对应 skill 自身说明执行。
- 若 skill 文档中给出了临时产物目录规则，应将该规则视为相对于 `.tmp/` 的子路径规则，而不是写到 skill 仓库或其他位置。
- 除非用户明确要求生成正式、可追踪的仓库内容，否则不要把这类产物直接写到仓库正式位置。

## Pre-Commit Gates

- agent 每次提交代码前，都必须运行统一门禁入口：`python scripts/pre_commit_gate.py`
- 只要任一门禁失败，就不要提交，先修复失败项。
- 具体门禁项由 `scripts/pre_commit_gate.py` 统一编排；不要绕过这个入口单独挑选运行。

## Registered Skills

### `skills/architecture_4-1`

- 加载路径：`skills/architecture_4-1/SKILL.md`
- skill 名称：`generate-3plus1-diagrams`
- 主要用途：分析目标仓库并生成 3+1 / 4+1 架构视图的可编辑 `.drawio` 图，以及对应的导出预览和校验结果

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求分析某个代码仓库的架构
- 用户要求生成架构图、模块图、组件关系图或 draw.io 图
- 用户明确提到 3+1、4+1、逻辑视图、开发视图、运行时视图、用例视图
- 用户希望基于代码仓库梳理模块边界、组件关系、运行路径或用户用例结构

当任务只是修改业务代码、修文档、修脚本、维护仓库骨架，且不涉及架构视图产出时，不应加载这个 skill。

使用这个 skill 时：

- 先读取 `skills/architecture_4-1/SKILL.md`
- 若任务会产生中间稿、日志、草图或阶段性结果，必须以 `.tmp/` 为工作根目录，并按该 skill 的目录约定拼接子路径
- 若用户明确要求分析当前仓库，也应把本仓库视为目标仓库，但临时架构产物仍必须落在 `.tmp/` 下

### `skills/hw-ppt-gen`

- 加载路径：`skills/hw-ppt-gen/SKILL.md`
- skill 名称：`huawei-pptx-generator`
- 主要用途：基于网页、Markdown、论文解析结果、仓库分析、纯文本或用户 prompt，生成华为风格的新 `.pptx` deck，并通过内置硬规则 QA、导出图片和视觉检查完成交付前校验

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求创建、生成、编写、重做或导出 PPT / PowerPoint
- 用户要求基于已有材料生成华为风格 PPTX
- 用户要求制作论文汇报、技术汇报、方法介绍、benchmark 评审、业务材料或技术 deck
- 用户要求使用华为视觉风格、华为红灰配色、中文正文或可导出的 PPTX 交付物
- 用户明确要求检查 PPT 布局安全性、文字是否溢出、是否裁切、是否重叠，且任务目标是生成新 deck

当任务只是整理普通文档、写纯文本大纲、修改代码或处理与 PPT 无关的内容时，不应加载这个 skill。该 skill 不用于深度编辑、合并、拆分或修复已有 PPT；这类任务应先确认是否需要改为“重新生成新 deck”。

使用这个 skill 时：

- 先读取 `skills/hw-ppt-gen/SKILL.md`
- 若任务会产生中间稿、图片、图表素材、生成脚本、检查结果、导出图片或阶段性 PPT，必须以 `.tmp/` 为工作根目录，并按该 skill 的 `.tmp/<deck>/` 目录约定拼接子路径
- 生成 PPT 后，应按该 skill 的要求运行参考图审阅、内容 QA、硬规则 QA、PPTX 图片导出和视觉 QA，再交付结果

### `skills/ppt-deep-search`

- 加载路径：`skills/ppt-deep-search/SKILL.md`
- skill 名称：`ppt-deep-search`
- 主要用途：在生成 PPT 之前，和用户进行 human-in-the-loop 深度研究，把论文、网页、Markdown、PDF 解析结果、仓库分析或纯文本材料整理成可供下游 PPT skill 消费的 `Storyline Brief`

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求在做 PPT 前先梳理研究问题、读者认知路径、故事线或论证结构
- 用户要求把材料转成章节逻辑、页面角色、页面标题、核心观点、claim/evidence/implication 结构
- 用户要求明确证据图、参考图、表格、截图的使用策略，例如原样使用、摘要重组、背景理解或舍弃
- 用户要求为技术汇报、论文汇报、业务材料或方案 deck 做前置内容规划，而不是直接生成 PPTX
- 用户明确提到 Deep Research、Storyline Brief、读者认知路径、金字塔结构、证据地图或反幻觉证据审核

当任务只是生成最终 PPTX、做华为视觉渲染、选择具体版式、导出图片、检查页面重叠裁切或执行 PPT 硬规则 QA 时，不应单独加载这个 skill；这些属于 `skills/hw-ppt-gen` 的职责。该 skill 也不应输出 `visual_anchor.kind`、`template`、`contentLayout`、字号、配色、几栏布局或渲染器等表达层字段。

使用这个 skill 时：

- 先读取 `skills/ppt-deep-search/SKILL.md`
- 若任务会产生研究草稿、材料清单、Storyline Brief 或 QA 结果，必须以 `.tmp/` 为工作根目录，例如写入 `.tmp/ppt-deep-search/<task-name>/`
- 最终交给 PPT skill 前，必须把 Storyline Brief 保存为 Markdown，并运行 `python skills/ppt-deep-search/scripts/validate_storyline_brief.py <brief.md> --min-page-content-chars 220`
- 若 QA 脚本报告格式缺失、页面信息密度不足、证据来源不清、开放问题缺失或包含表达层字段，应先修正 brief 再进入 PPT 生成

### `skills/grobid_pdf_skill`

- 加载路径：`skills/grobid_pdf_skill/SKILL.md`
- skill 名称：`grobid-docling-pdf`
- 主要用途：解析论文或技术 PDF，结合 GROBID 的学术文本结构与 Docling 的图表图片导出，生成可供下游 agent 理解和引用的 TEI/XML 包

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求解析、读取、理解、结构化分析论文 PDF 或技术 PDF
- 用户要求从 PDF 中提取标题、摘要、正文、章节、引用、参考文献、图表或表格图片
- 用户希望增强 agent 对 PDF 内容的理解效果，或要求生成供后续任务使用的 XML / TEI 中间表示
- 用户要求把 PDF 中的图、表与正文引用关系整理成可追踪的结构化结果

当任务只是生成 PPT、修改代码、整理普通文档，且不需要重新解析 PDF 内容时，不应加载这个 skill；但基于论文 PDF 生成 PPT 前，可先使用该 skill 生成结构化解析结果，再交给 PPT skill 使用。

使用这个 skill 时：

- 先读取 `skills/grobid_pdf_skill/SKILL.md`
- 若任务会产生中间解析文件、导出图片、XML、校验报告或归档结果，必须以 `.tmp/` 为工作根目录，并按该 skill 的默认目录约定写入 `.tmp/pdf_xml/<paper-name>/`
- 运行前应确认 GROBID 服务地址；默认使用 `http://localhost:8070`
- 对 born-digital 论文 PDF 默认不要开启 OCR；仅在扫描版 PDF 场景下按 skill 说明启用 OCR
- 交付结果时应报告最终 XML 路径、图片目录和数量、中间结果归档路径，以及校验状态

### `skills/send-qq-email`

- 加载路径：`skills/send-qq-email/SKILL.md`
- skill 名称：`send-qq-email`
- 主要用途：通过 QQ 邮箱 SMTP 发送或预演 UTF-8 纯文本 / HTML 邮件，并生成 `.eml` 快照和结构化发送结果

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求发送、测试、预览或 dry-run QQ 邮箱邮件
- 用户要求配置、验证或排查 QQ Mail SMTP / 授权码邮件发送能力
- 用户要求生成 `.eml` 邮件快照、发送测试邮件或复用轻量邮件发送脚本
- 用户明确提到 `SMTP_USERNAME`、`SMTP_PASSWORD`、`SMTP_TO`、QQ 邮箱授权码或 `send_qq_email.py`

当任务只是整理普通文档、生成 PPT、解析 PDF、分析架构或修改与邮件发送无关的代码时，不应加载这个 skill。

使用这个 skill 时：

- 先读取 `skills/send-qq-email/SKILL.md`
- 涉及真实发送时，若用户意图或收件人不明确，应先确认；配置检查、预览和验证任务默认使用 `--dry-run`
- 不要打印、记录或提交 SMTP 密码、QQ 邮箱授权码等凭据
- 若任务会产生邮件快照、发送结果或调试日志，必须以 `.tmp/` 为工作根目录，例如写入 `.tmp/send-qq-email/`
