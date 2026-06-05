---
date: 2026-05-19
topic: huawei-content-aware-layout
---

# Huawei Content-Aware Layout Brainstorm

## Problem Frame

当前 PPT 生成器在处理高信息密度 summary / content 页时，容易在两个方向之间摇摆：一边是忠实保留 brief 内容，导致文字冗长、图文失衡；另一边是机械套用华为参考页，恢复了红灰母版语言，但也恢复了等宽分栏、底部空洞和图文稀疏。

这次原型验证出的目标是：**用华为 PPT 的视觉语言承载内容感知布局**。`05 内容 二分栏`、`06 内容 偏分栏`、`07 内容 三分栏` 提供红色标题、分析总结、模块框、灰线、箭头和高密信息秩序；但版型选择、列宽、图文比例、底部密度和文本压缩必须由内容决定。

归档原型：

- `05 内容 二分栏`: [prototype-two-column.html](prototype-two-column.html), [screenshot-two-column.png](screenshot-two-column.png)
- `06 内容 偏分栏`: [prototype-biased-column.html](prototype-biased-column.html), [screenshot-biased-column.png](screenshot-biased-column.png)
- `07 内容 三分栏`: [prototype.html](prototype.html), [screenshot-huawei-dense.png](screenshot-huawei-dense.png)

---

## Actors

- A1. Deck-generation agent: 读取 `ppt_content_brief.md`、选择布局、生成 PPTX。
- A2. PPT layout renderer: 根据布局契约放置标题、分析总结、视觉证据、文本块、数据块和箭头。
- A3. Reviewer / platform reader: 扫描 summary 页，判断场景、机制、结果是否可信且可读。

---

## Key Flows

- F1. Content-aware layout family selection
  - **Trigger:** brief 中 content / summary page 有 1-3 个核心观点，并包含证据图、KPI、机制关系或生产结果。
  - **Actors:** A1, A2
  - **Steps:** 先压缩可见文字，再评估每个观点的视觉证据、文本预算、证据图宽高比、信息重量和叙事关系；在 `two_column`、`biased_column`、`three_column` 中选择版型；按内容权重动态调整内部空间；用结构化小模块补足底部密度。
  - **Outcome:** 页面保留华为风格，但不会因为机械套版造成图文错位、证据图不可读或大面积无意义留白。
  - **Covered by:** R1, R2, R3, R4, R5, R6

- F2. Visual QA review
  - **Trigger:** PPTX 导出为图片后进入人工或自动视觉检查。
  - **Actors:** A2, A3
  - **Steps:** 对照参考页检查华为母版语言；对照归档原型检查图文平衡、信息密度和文本压缩；若出现空洞、冗长或证据图不可读，回到布局选择或文本压缩阶段。
  - **Outcome:** QA 不只判断是否符合模板，还判断是否实现高密、可读、有层级的信息设计。
  - **Covered by:** R6, R7, R8

---

## Requirements

**Design principle**

- R1. Summary 页必须先做编辑压缩，再做排版；完整 brief 内容保留在 plan、notes 或审计材料里，可见页面只保留可扫描的核心判断。
- R2. 高信息密度不等于塞更多长句；页面应通过多层级、多证据、多结构增加密度，例如 KPI、对照表、小灰框、图注和判断句。
- R3. 参考页只提供视觉语言，不提供不可变几何；`05/06/07` 的区域比例、视觉高度和文本区域必须允许在版型边界内按内容权重动态调整。

**Huawei visual language**

- R4. 页面应保留华为正文页关键元素：红色主标题、右上章节 tab、标题红线、`分析总结` 横条、红色模块标题栏、细灰边框、灰色内容结构，以及在需要表达跨模块流向时使用红色流程箭头。
- R5. 页面应避免网页化海报感：不使用大阴影、渐变装饰、满版 hero、圆角卡片堆叠或脱离模板的视觉效果。

**Content-aware layout**

- R6. 布局选择必须同时考虑观点数量、可见文本长度、证据图宽高比、证据图最小可读尺寸、KPI 数量、叙事关系和底部密度，而不是只按观点数量选择 `two_column`、`biased_column` 或 `three_column`。
- R7. `two_column` 适合“主证据图 + 对照/结果压缩”的页面：左右两栏都应承担完整信息模块，允许一栏主图更高、另一栏用机制对照 + KPI 形成第二证据层。
- R8. `biased_column` 适合“单一主图是核心证据”的页面：左侧大视觉区必须优先保证图可读，右侧一到三张解释卡负责机制、边界、KPI 或决策含义，不能把长段正文塞进左侧主图区。
- R9. `three_column` 适合“三个并列观点或递进阶段”的页面：允许非等宽列，例如场景证据图更宽、机制图稍窄、结果栏承载 KPI + 曲线 + 结论；列宽应服务图文重量，而不是追求模板均分。
- R10. 每个模块底部不应出现无意义空白；当内容不足时，优先补充结构化信息块，而不是拉长 bullet 或放大无关装饰。

**Text and evidence**

- R11. 可见文本应控制为短标签 + 判断句，避免把 brief 的正文段落直接塞入模块。
- R12. 证据图必须保持可读尺寸；如果源图在模块中不可读，应裁剪、重绘、拆分子图或改用 KPI / 表格摘要，而不是硬塞原图。
- R13. 图文关系应明确：场景图回答“为什么有浪费”，机制图回答“抢占点如何前移”，结果图和 KPI 回答“生产收益是否成立”。

---

## Acceptance Examples

- AE1. **Covers R1, R2, R10, R11.** Given Aegaeon summary brief contains long scenario/mechanism/result paragraphs, when generating the summary page, the visible page uses short claim lines, KPI cards, a compact comparison table, and dense-note boxes instead of copying long paragraphs.
- AE2. **Covers R3, R4, R9.** Given a slide uses `07 内容 三分栏` as the visual family, when the evidence weights differ by column, the renderer may use non-equal column widths while preserving red title bars, gray outlines, analysis summary, and flow arrows.
- AE3. **Covers R6, R7, R12, R13.** Given Figure 1 is the strongest scene evidence and Figure 2 plus KPI values are secondary evidence, when choosing `05 内容 二分栏`, the left column receives a larger readable Figure 1 and the right column compresses mechanism + result into structured blocks.
- AE4. **Covers R6, R8, R12, R13.** Given Figure 2 is the main mechanism evidence, when choosing `06 内容 偏分栏`, the left large visual area preserves Figure 2 readability and the right cards carry TTFT/TBT, 0.8s overhead, and production KPI interpretation.

---

## Success Criteria

- A reviewer can understand the summary page by scanning the title, analysis band, module titles, KPI numbers, and red-highlighted labels without reading long prose.
- The generated page visually reads as Huawei-style PPT, not as a generic web dashboard or marketing poster.
- The page feels high-density but ordered: minimal empty bottom space, no overlong bullet list, and every visual/text block has a clear job.
- A downstream implementation plan can translate the principle into layout-family selection, layout scoring, text-budget checks, image-size checks, and visual QA without inventing the design direction.

---

## Scope Boundaries

- This brainstorm defines the target design principle and acceptance examples; it does not implement the PPT generation code.
- The prototype is a static HTML proof, not a replacement for PPTX rendering.
- The goal is not pixel-perfect copying of `05 内容 二分栏.png`、`06 内容 偏分栏.png` or `07 内容 三分栏.png`; the goal is to reuse their Huawei visual language while correcting content-specific layout failures.
- This does not require changing visual-anchor semantic boundaries: source images should still remain `Evidence`, generated/transcribed tables should still remain `Matrix/table`, and visible prose remains PPT text.

---

## Key Decisions

- Use content-aware layout-family selection across `05/06/07`: the family is chosen by evidence structure, not by viewpoint count alone.
- Use dynamic weighting inside each Huawei family: equal columns and fixed visual heights are defaults, not requirements.
- Treat bottom density as a first-class layout target: empty space should become structured information when the source material supports it.
- Prefer structural compression over prose compression alone: KPI cards, mini tables, dense notes, and short claim lines often outperform additional bullet text.
- Keep Huawei style constraints visible: red/gray palette, thin lines, square modules, compact typography, no decorative web effects.

---

## Dependencies / Assumptions

- The implementation should remain consistent with `docs/architecture_design.md`: layout, visual anchors, and PPT text layer stay separate.
- The reference families are `assets/slides_ref/05 内容 二分栏.png`, `assets/slides_ref/06 内容 偏分栏.png`, and `assets/slides_ref/07 内容 三分栏.png`; they should be interpreted as style references and layout families rather than fixed grids.
- The archived HTML files and screenshots are design evidence for the Aegaeon content-aware layout family and can serve as regression references for future layout work.

---

## Outstanding Questions

### Deferred to Planning

- [Affects R6, R7, R8, R9][Technical] What scoring function should choose between `two_column`, `biased_column`, and `three_column` from text length, image aspect ratio, evidence importance, and narrative relationship?
- [Affects R10][Technical] Which structured filler blocks should be allowed by the existing content layout contract without creating layout-specific visual roles?
- [Affects R12][Needs research] Should source figure cropping/redrawing be handled before planning, inside `Evidence`, or as a derived evidence asset recorded in the manifest?

---

## Next Steps

-> `/ce-plan` for structured implementation planning.
