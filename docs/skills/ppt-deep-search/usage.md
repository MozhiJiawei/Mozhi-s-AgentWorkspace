# 使用方式

`ppt-deep-search` 不是一轮总结器，而是生成 PPT 前的研究对齐流程。它先让人确认读者、问题、证据边界和故事线，再输出下游 PPT skill 可消费的内容包。

## 适用场景

使用这个 skill 处理以下任务：

- 从论文、网页、Markdown、仓库分析、PDF、笔记或原始材料中整理 PPT 观点。
- 在正式做 PPTX 之前，先确认读者认知路径、SCQA、章节逻辑和页面观点。
- 把来源证据、推理边界、用户审批和 QA 记录保存在审计文件中，避免下游 PPT 文案混入内部工作记录。

不要用它做 PPTX 视觉渲染、版式模板、字体配色、导出或视觉 QA。这些属于下游 PPT 制作 skill。

## 标准流程

默认走 human-in-the-loop：

1. 确认目标读者、读者当前判断、希望改变的判断、最终用途和来源集合。
2. 做 source understanding，必要时生成 `review/source_understanding_review.html`，让用户先审研究理解、证据、比较对象和边界。
3. 确认 SCQA 和顶层 summary page 表达，包括 `页面标题`、`标题说明`、`分析总结`。
4. 单独确认页数口径，不提前生成目录。
5. 确认 Table of Contents，目录最多 3 个章节项，目录项是导航文案，不是证据地图。
6. 按章节逐步确认页面观点层：页面标题、标题说明、分析总结、正文支撑和参考图片策略。
7. 确认最终硬约束后，写入 `ppt_content_brief.md` 和 `research_audit.md`。

每个阶段都有两个门：先获得用户 approval，再把该阶段基线保存到 `<workspace-root>/baselines/`。已批准的基线不能被静默重写；如果后续证据要求调整，需要重新请用户确认并记录在 `Approval Log`。

## 工作目录

一次运行只使用一个 `workspace-root`：

- 默认路径：`.tmp/ppt-deep-search/<task-name>/`
- forward-test 路径：`.tmp/forward-tests/<case-id>/<run-id>/`
- 用户指定输出目录时，以用户指定目录为准

所有临时笔记、baseline、HTML review、资产和 QA 输出都放在这个目录下。最终交付物固定为：

- `<workspace-root>/ppt_content_brief.md`
- `<workspace-root>/research_audit.md`

## 交付物

`ppt_content_brief.md` 是下游 PPT 文案包，只放可直接引用、改写或放进页面的内容：

- Deck Metadata
- Summary Page
- Table of Contents
- Page Content

`research_audit.md` 是内部审计文件，保存不该进入 PPT 文案的内容：

- 读者和信念变化
- source understanding
- pyramid outline
- Claim/Evidence/Implication
- source locators 和 usage policy
- supplemental research
- assumptions/open questions
- approval log

如果任务需要网页证据，先使用仓库内 `web-article-capture/SKILL.md` 生成本地 Browser evidence package，再让 HTML review 和 audit 引用本地正文、原始正文图片和 manifest。不要用搜索摘要、raw HTML、`curl` 抓取结果、手写网页摘录或渲染截图替代这个证据包。

## 校验命令

HTML review 写完、请求用户 approval 前，尽量运行：

```powershell
python scripts/validate_web_evidence_package.py <workspace-root>/review/report-data.json --require-images when-indexed
python scripts/validate_html_review_data.py <workspace-root>/review/report-data.json
python scripts/validate_html_review.py <workspace-root>/review/source_understanding_review.html
```

如果是产品发布、技术公告、官方博客等多图网页，使用更严格的图片门：

```powershell
python scripts/validate_web_evidence_package.py <workspace-root>/review/report-data.json --require-images always --min-image-sources 1
```

最终 brief 写完后，按页数口径运行：

```powershell
python scripts/validate_ppt_content_brief.py <workspace-root>/ppt_content_brief.md --expected-pages <total-pages>
```

如果 brief 中的 `参考图片` 使用本地绝对路径，测试或 forward judgment 可加：

```powershell
python scripts/validate_ppt_content_brief.py <workspace-root>/ppt_content_brief.md --expected-pages <total-pages> --allow-absolute-paths
```

仓库级依赖与契约检查：

```powershell
python verify_dependencies.py
```
