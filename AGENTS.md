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

### `skills/gh-issue-comment-monitor`

- 加载路径：`skills/gh-issue-comment-monitor/SKILL.md`
- skill 名称：`gh-issue-comment-monitor`
- 主要用途：监控 GitHub Issue 评论更新，只拉取相对本地 checkpoint 的最新回复，避免反复加载完整 issue 历史

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求重新检查某个 GitHub Issue 是否有新回复
- 用户要求读取 issue 最新评论、最新回复或新增评论
- 用户要求监控、跟进、轮询某个 GitHub Issue 评论区
- 用户希望避免重复读取完整 issue 历史，只处理新评论或最新评论
- 用户明确提到 `gh-issue-comment-monitor`、`check_issue_updates.py` 或 `get_latest_comments.py`

当任务只是创建 issue、修改代码、处理 PR 评论或需要完整 issue 背景重建时，不应仅依赖这个 skill；只有在需要轻量获取 issue 评论增量时使用。

使用这个 skill 时：

- 先读取 `skills/gh-issue-comment-monitor/SKILL.md`
- 状态文件和本轮 updates 文件必须写入 `.tmp/gh-issue-comment-monitor/`
- 优先使用该 skill 的脚本读取增量评论；只有缺少 checkpoint 或任务确实需要重建上下文时，才读取完整 issue 历史
- 只有在已成功处理返回评论后，才使用 `--update-state` 更新本地 checkpoint

### [beta] `skills/architecture_4-1`

- 加载路径：`skills/architecture_4-1/SKILL.md`
- skill 名称：`generate-3plus1-diagrams`
- 主要用途：[beta] 分析目标仓库并生成 3+1 / 4+1 架构视图的可编辑 `.drawio` 图，以及对应的导出预览和校验结果

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

### `skills/hw-ppt-gen-html`

- 加载路径：`skills/hw-ppt-gen-html/SKILL.md`
- skill 名称：`hw-ppt-gen-html`
- 主要用途：基于材料生成 HTML PPT、网页 slides、deck 或 HTML 演示文稿，并在完成后导出 PNG、委派独立视觉 QA checker 校验

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求创建、生成、编写、重做或导出 PPT、slides、deck、演讲稿页面或技术汇报页面
- 用户要求生成 HTML PPT、HTML slides、网页演示文稿、Web deck 或可在浏览器中打开的幻灯片
- 用户要求基于已有材料生成华为风格汇报、华为红灰配色汇报、中文正文或可导出的演示文稿
- 用户要求用 HTML/CSS/前端方式制作 deck、slides、演讲稿页面或技术汇报页面
- 用户提供 `ppt_content_brief.md`，并希望继续生成 PPT / slides / deck
- 用户要求对已完成的 HTML 演示文稿进行导出 PNG 和独立视觉 QA
- 用户明确提到 `hw-ppt-gen-html`、`html-ppt-skill`、`render_html_ppt.py` 或 `html-ppt-visual-qa-rubric.md`

当任务只是整理普通文档、写纯文本大纲、修改代码或处理与 PPT 无关的内容时，不应加载这个 skill。

使用这个 skill 时：

- 先读取 `skills/hw-ppt-gen-html/SKILL.md`
- 若任务会产生中间稿、HTML、导出图片、视觉 QA 记录或阶段性结果，必须以 `.tmp/` 为工作根目录，例如写入 `.tmp/hw-ppt-gen-html/<task-name>/`
- 完成 HTML 演示文稿后，必须按该 skill 要求运行 `scripts/render_html_ppt.py` 导出 PNG，并委派独立视觉 QA checker；`visual-qa.md` 必须包含逐页 `Primary Visual Checks`

### `skills/ppt-deep-search`

- 加载路径：`skills/ppt-deep-search/SKILL.md`
- skill 名称：`ppt-deep-search`
- 主要用途：在生成 PPT 前做人机协同的深度研究、观点对齐、故事线规划和证据审计，产出 `ppt_content_brief.md` 与 `research_audit.md` 供后续 PPT 生成 skill 使用

只有当人类明确提到“PPT深度研究”时，agent 才应加载并使用这个 skill。用户只是说“做 PPT”“生成 PPT”“制作 PPT”“PPT 汇报”或类似普通 PPT 制作需求时，不应触发该 skill，应直接使用 `skills/hw-ppt-gen-html`。

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户明确要求进行“PPT深度研究”
- 用户明确要求在生成 PPT 前先做深度研究、观点对齐、证据审计或故事线规划，并且使用了“PPT深度研究”这个触发词
- 用户明确要求基于材料先产出 PPT Content Brief / Research Audit，再交给 PPT 生成流程
- 用户明确提到 `ppt-deep-search`、`ppt_content_brief.md`、`research_audit.md` 或 `validate_ppt_content_brief.py`

使用这个 skill 时：

- 先读取 `skills/ppt-deep-search/SKILL.md`
- 所有临时笔记、基线、草稿、QA 输出和最终 handoff 文件必须写入 `.tmp/ppt-deep-search/<task-name>/`
- 完成深度研究后，必须按该 skill 要求运行 `validate_ppt_content_brief.py` 校验 `ppt_content_brief.md`
- 若用户随后要求生成 PPT，应把已通过校验的 `ppt_content_brief.md` 作为 `skills/hw-ppt-gen-html` 的输入；不要在深度研究阶段做视觉模板、字体、配色、版式或导出决策	

### `skills/web-article-capture`

- 加载路径：`skills/web-article-capture/SKILL.md`
- skill 名称：`web-article-capture`
- 主要用途：使用 Codex in-app Browser 抽取网页 article/main 正文文本和原始正文图片，生成可供下游 agent 使用的紧凑 source package

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求抓取、抽取、保存或打包网页正文内容
- 用户要求把网页文章、官方页面、博客、公告、文档页或媒体丰富页面整理成下游可引用的 source package
- 用户需要网页原始正文图片、图表、图注或图片与附近文本的对应关系
- 用户明确提到 `web-article-capture`、`validate_capture_package.py`、网页 capture package 或 `source.md`

当任务只是检索网页事实、总结少量网页信息、制作 PPT、解析 PDF、处理 GitHub Issue 或无需浏览器渲染正文和图片资产时，不应加载这个 skill。

使用这个 skill 时：

- 先读取 `skills/web-article-capture/SKILL.md`
- 若任务会产生 source package、图片、review.html、日志或调试产物，必须以 `.tmp/` 为工作根目录，例如写入 `.tmp/web-article-capture/<task-name>/`
- 需要真实网页抓取时，应按 skill 说明优先使用 Codex in-app Browser；被阻断、超时或只能部分抓取时，要在 `source.md` 记录 capture mode、blocked stage 或 fallback source
- 交付前必须运行 `python skills/web-article-capture/scripts/validate_capture_package.py <output-root> --require-images when-referenced`

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
