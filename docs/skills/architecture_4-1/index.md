# 架构概览

本页复用仓库内现有架构规则文档的内容，作为主仓三段论里的架构概览入口。更细的建模约束继续维护在 `references/` 下。

## Skill 定位

`generate-3plus1-diagrams` 用于分析目标仓库，并生成符合 3+1 / 4+1 架构视图模型的可编辑 `.drawio` 图。它把一次架构交付拆成两个阶段：

1. 视图建模阶段：每个视图产出中间 JSON 和证据/假设说明。
2. 主 Agent 完成阶段：统一渲染 `.drawio`，导出 PNG 预览，并运行 XML、视觉管线和人工审阅辅助检查。

临时产物默认放在目标项目根目录的 `.tmp/generate-3plus1-diagrams/<repo-name>/<view>/` 下，而不是写回 Skill 仓库或目标仓库源码目录。

## 3+1 / 4+1 视图

以下内容来自 `references/3plus1-rules.md` 和 `references/view-checklists.md`。

### 逻辑视图

逻辑视图解释系统的主要职责：

- 业务域
- 主要服务或子系统
- 外部系统
- 稳定依赖方向

它避免低层实现噪音，除非这些实现细节能解释关键边界。建模时要判断候选元素是真职责，还是只是文件夹、框架或 helper 代码；多个文件共同实现一个职责时，应折叠成一个逻辑元素。

### 开发视图

开发视图解释代码库如何被开发者维护：

- 仓库
- package
- module
- shared library
- ownership 或 layering 边界

它优先表达编译期、打包期、import 期关系，而不是运行时聊天记录。若用户指定了核心用例，开发视图应先过滤到实现该用例的代码，再补充必要的共享支撑模块。

### 运行视图

运行视图解释运行时协作：

- 请求路径
- 异步消费者
- 队列
- 缓存
- 任务和调度
- 跨服务协作

它需要和逻辑视图保持架构并行：从有证据的运行参与者和交互出发，区分显式关系与推断关系。分支只在能解释鉴权、失败、重试、fallback、状态迁移等关键行为时展示。

### 用例视图

用例视图把其他视图串起来。它优先选择能跨越重要边界、暴露核心职责、解释架构形态的代表性用例。

当系统存在大量一等用户可见模式时，用例视图作为 4+1 模型的索引：

- 枚举核心用例集
- 渲染全量用例图，而不只画一条典型旅程
- 用 P0/P1/P2 区分最终用户能力、直接支撑能力和维护治理能力

经典用例图只表达 actor、系统边界、复用目标和条件目标；内部组件和逐步运行编排应进入逻辑视图或运行视图。

## 协作边界

主 Agent 负责监督、渲染、验证和交付，不直接替代各视图的架构分析。视图拥有者需要写出：

- `<view>-view.json`
- `evidence-assumptions.md`

主 Agent 在接受模型前，应检查证据、假设、遗漏、跨视图一致性和参考图视觉基线。渲染阶段统一使用：

```bash
python scripts/render_drawio.py <json-path> --output-dir <view-dir> --export-previews --preview-dir <view-dir>\exports --preview-format png
```

交付前再运行：

```bash
python scripts/tools/validate_visual_pipeline.py <drawio-or-output-dir>
```

## 关键参考

- `references/drawio-dsl.md`：中间 JSON 模型的 schema 权威来源。
- `references/renderer-contract.md`：渲染器支持的 view、kind、alias 和默认行为。
- `references/style-profiles.md`：图形风格和颜色约束。
- `references/ref-usage.md`：如何使用 `ref/` 作为视觉基线。
- `references/logic-view-patterns.md`：逻辑视图建模策略。
- `references/development-view-patterns.md`：开发视图交付契约。
- `references/runtime-view-patterns.md`：运行视图建模策略。
- `references/use-case-view-patterns.md`：用例视图建模策略。

## 子仓文档导航

- [能力展示](./reference.md)
- [使用方式](./usage.md)
- [架构概览](./)
