# 使用方式

Huawei PPTX Generator 是一个 Codex skill 资源包。运行时 agent 应先读取 `SKILL.md`，再按 `references/` 中的交付标准、brief 合同、版式标准、证据 schema 和 generated visual schema 生成 PPTX。

## 输入材料

支持的输入包括：

- 网页、Markdown、论文解析结果、仓库分析或纯文本材料；
- 候选 brief 或已经通过上游检查的 deck plan；
- source figures、screenshots、tables 和其它可追溯证据。

正文内容页必须有真实视觉锚点。source figures 和 screenshots 应进入 `Evidence`，生成图应使用 `visual_anchor` 的语义模板，表格、KPI 卡片、能力矩阵、能力栈和 heatmap 应作为 `supporting_component`，不能冒充视觉锚点。

## 生成流程

1. 读取 `SKILL.md` 和相关 `references/*.md`。
2. 将材料整理成 `.tmp/<deck>/<deck>_plan.json`，记录每页的 `contentLayout`、`visual_anchor`、`supporting_component` 和可编辑文本层。
3. 用 `scripts/pptx/hw_visual_anchor_slide.js` 和 `scripts/pptx/hw_diagram_helpers.js` 生成 PPTX。
4. 写出 visual-anchor manifest，确保每个正文内容页的真实视觉锚点和 supporting component 都可被 QA 对账。
5. 用 PowerPoint COM 导出 PNG，人工检查排版、证据可读性、遮挡、文字压缩和页脚/source note。
6. 运行硬规则 QA，确认 plan、manifest、PPTX 和导出证据一致。

## 产物目录

交付过程中的生成产物写入：

```text
.tmp/<deck>/
```

常见产物包括：

- `<deck>.pptx`: 最终 PPTX；
- `<deck>_plan.json`: 生成计划；
- `<deck>_visual_anchor_manifest.json`: 视觉锚点和 supporting component manifest；
- `<deck>.qa.json`: QA 输出；
- `<deck>_slides/` 或 `slides/`: PowerPoint COM 导出的 PNG；
- `contact_sheet.png`: 多页预览图，适合做交付说明和 forward-test 展示。

## 常用命令

生成样例 deck：

```bash
npm run sample
```

校验样例 deck：

```bash
npm run check-sample
```

导出样例 deck 图片：

```bash
npm run export-sample
```

开发态 smoke suite：

```bash
npm run smoke
```

`npm run smoke` 会覆盖 brief consumption、visual-anchor contract、文本高度估算、QA 规则回归、content layout smoke、样例 deck、diagram smoke 和 PowerPoint COM 导出。PowerPoint COM 是 Windows 上的质量门槛；如果 PowerPoint 导出后锁文件，应关闭残留 `POWERPNT` 进程再重跑。

## Forward Test

正式 forward-test case 位于：

```text
forward-tests/huawei-ppt-gen/<case-id>/
```

当前正式 case：

- `aegaeon-content-aware-layout`
- `tidar-evidence-readability`

运行方式是人工编排：主 agent 读取 `forward-tests/huawei-ppt-gen/main-agent-prompt.md`，把每个 case 的 `candidate/prompt.md`、`candidate/input/`、仓库 `SKILL.md`、`docs/architecture_design.md` 和运行时 references/assets 交给独立候选 agent；judge-only 的 `fixture-manifest.md`、`judge/rubric.md` 和 expected examples 留在主 agent 上下文中。
