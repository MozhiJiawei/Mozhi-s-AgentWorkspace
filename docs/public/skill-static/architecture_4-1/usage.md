# 使用方式

## 适用场景

当用户希望从一个源码仓库生成架构图时使用本 Skill。典型请求包括：

- 生成逻辑视图、开发视图、运行视图或用例视图。
- 只围绕某个核心用例生成一张开发视图。
- 从已有中间 JSON 重新渲染 `.drawio` 和 PNG 预览。
- 对生成图进行 XML、导出和视觉质量检查。

## 输入材料

最小输入是目标仓库路径和需要生成的视图。若用户没有指定视图，优先确认是否需要完整 3+1 / 4+1 交付。

推荐补充材料：

- 用户关心的核心用例或业务问题。
- 需要忽略的目录，例如 generated、vendor、cache、实验输出。
- 目标语言，中文任务默认使用中文标签和说明。
- 是否只要 `.drawio`，还是同时需要 PNG 预览和打包交付。

## 输出目录

临时产物放在目标项目根目录：

```text
.tmp/generate-3plus1-diagrams/<repo-name>/<view>/
```

每个视图目录通常包含：

- `<view>-view.json`：中间模型。
- `evidence-assumptions.md`：证据、假设、遗漏和剪枝说明。
- `<view>-view.drawio`：可编辑 draw.io 文件。
- `exports/*.png`：导出预览。
- `exports/visual-review.md`：视觉审阅辅助信息。

用例视图会额外产出：

- `use-case-catalog-view.drawio`
- `exports/use-case-catalog-view.png`

运行视图可能按 primary path 产出多张 `.drawio` 和 PNG。

## 推荐流程

1. 读取 `SKILL.md` 和相关 `references/*.md`。
2. 为每个请求的视图建立独立视图建模任务。
3. 每个视图先产出 JSON 和 `evidence-assumptions.md`。
4. 主 Agent 审查模型是否符合对应视图规则。
5. 使用 `scripts/render_drawio.py` 渲染 `.drawio` 和 PNG。
6. 使用 `scripts/tools/validate_visual_pipeline.py` 做 XML、导出和预览检查。
7. 对照 `ref/` 和 `references/style-profiles.md` 做最终视觉审阅。

## 常用命令

渲染单个中间模型：

```bash
python scripts/render_drawio.py .tmp/generate-3plus1-diagrams/<repo>/<view>/<view>-view.json --output-dir .tmp/generate-3plus1-diagrams/<repo>/<view> --export-previews --preview-dir .tmp/generate-3plus1-diagrams/<repo>/<view>/exports --preview-format png
```

验证单个 `.drawio`：

```bash
python scripts/tools/validate_drawio.py .tmp/generate-3plus1-diagrams/<repo>/<view>/<view>-view.drawio
```

运行完整视觉管线：

```bash
python scripts/tools/validate_visual_pipeline.py .tmp/generate-3plus1-diagrams/<repo>/<view>/<view>-view.drawio
```

导出已有图：

```bash
python scripts/tools/export_diagrams.py .tmp/generate-3plus1-diagrams/<repo>/<view>/<view>-view.drawio --output-dir .tmp/generate-3plus1-diagrams/<repo>/<view>/exports --format png
```

## 交付检查

交付前至少确认：

- 每个请求视图都有 JSON、证据说明、`.drawio` 和 PNG。
- `evidence-assumptions.md` 明确区分事实、推断和刻意省略。
- 逻辑视图讲职责，不退化成目录树。
- 开发视图讲维护单元、边界和依赖，不画运行链路。
- 运行视图讲请求、异步、缓存、任务、失败或状态迁移。
- 用例视图讲 actor 和用户目标，不把内部组件画成用例。
- PNG 非空，标签可读，布局不过密，颜色符合 `references/style-profiles.md`。
