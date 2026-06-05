# 能力展示

这里不讲内部实现，直接看这个 Skill 能不能把一个真实仓库讲清楚、画出来、交付成可编辑的架构图。

当前仓库还没有标准 `forward-tests/` case 目录，所以我在本仓 `.tmp/` 和 `D:\Agent Repo\Mozhi-s-AgentWorkspace\.tmp` 里找历史运行记录。现在整理出两个 case：`fireworks-tech-graph` 和 `dynamo-main`。文档只纳管页面直接依赖的 PNG 预览图，原始运行产物仍留在 `.tmp` 运行记录里。

## Case：fireworks-tech-graph

### 这个 case 是什么

`fireworks-tech-graph` 是一个“用自然语言生成技术图”的 Skill 仓库。用户给它一段系统、流程或 Agent 场景描述，它负责生成 SVG 技术图，并导出 PNG。

这次测试的目标不是让它再生成一张普通技术图，而是反过来分析这个仓库本身：看它有哪些用户能力、代码怎么组织、运行时怎么协作，并把这些内容画成 3+1 / 4+1 架构视图。

### 输入是什么

输入是一整个目标仓库，而不是几行配置：

- 仓库 README 和 Skill 说明，用来判断它对用户承诺了什么能力。
- `SKILL.md`，用来理解它实际要求 Agent 怎么工作。
- `scripts/`，用来理解图生成、校验和导出流程。
- `templates/`、`references/`、`fixtures/`，用来判断模板、风格规则和回归样例在系统里扮演什么角色。

### Prompt 是什么

这次没有找到独立的 forward-test prompt 文件。根据运行目录和交付件，可还原成下面这个任务：

```text
分析 fireworks-tech-graph 仓库，为它生成完整的 3+1 / 4+1 架构图。

需要覆盖：
- 用例视图：它面向哪些用户，提供哪些一等能力。
- 逻辑视图：系统由哪些核心职责组成。
- 开发视图：代码和资产如何被维护。
- 运行视图：用户触发出图、模板生成、校验导出、批量回归时，系统如何协作。

输出可编辑 draw.io 文件、PNG 预览，以及每张图的证据和假设说明。
```

### 我是怎么做的

先读仓库公开材料，判断“用户真正能感知的能力”是什么；再把内部文件夹整理成有意义的职责和维护单元，而不是把目录树硬画出来。

然后分别建模四类视图：

- 用例视图回答“它能帮谁做什么”。
- 逻辑视图回答“它靠哪些核心职责组成”。
- 开发视图回答“维护者改代码时该怎么看边界”。
- 运行视图回答“从一句自然语言到 SVG/PNG，中间发生了什么”。

最后把中间模型渲染成 `.drawio`，再导出 PNG 作为可检查的交付预览。

### 最终效果

#### 先看用户能力

这张图把 `fireworks-tech-graph` 面向用户的能力摊开：架构图、流程图、AI/Agent 图、UML 图、对比概念图，以及安装、配置、校验、回归测试这些支撑能力。

![fireworks-tech-graph use case view](deliverables/fireworks-tech-graph/use-case/use-case-view.png)

如果要看更完整的能力清单，还有一张表格版。它适合放进评审材料里，让人快速扫一遍“这个 Skill 到底覆盖了哪些场景”。

![fireworks-tech-graph use case catalog view](deliverables/fireworks-tech-graph/use-case/use-case-catalog-view.png)

#### 再看系统由什么组成

逻辑视图把仓库抽象成几个稳定职责：入口与宿主、技能编排、图结构规划、模板化生成、风格与图标知识、验证导出工具链、外部导出工具。

这张图的价值是让新维护者不用先钻进脚本细节，就能知道这个 Skill 的脑袋、手脚和质检环节分别在哪里。

![fireworks-tech-graph logic view](deliverables/fireworks-tech-graph/logic/logic-view.png)

#### 再看代码怎么维护

开发视图不按目录机械展开，而是按维护视角整理：入口契约、核心生成器、模板库、风格规范、回归样例、脚本工具链和展示资产。

它回答的是“我要改一个能力，应该动哪块；改完后谁会被影响”。

![fireworks-tech-graph development view](deliverables/fireworks-tech-graph/development/development-view.png)

#### 最后看运行时怎么流动

运行视图拆成四条典型路径。这样比把所有箭头塞进一张图更好读。

用户聊天触发出图：

![fireworks-tech-graph runtime dialogue skill output](deliverables/fireworks-tech-graph/runtime/dialogue-skill-output.png)

模板化生成 SVG：

![fireworks-tech-graph runtime template svg](deliverables/fireworks-tech-graph/runtime/template-svg.png)

脚本校验并导出 PNG：

![fireworks-tech-graph runtime validation export](deliverables/fireworks-tech-graph/runtime/validation-export.png)

批量回归测试：

![fireworks-tech-graph runtime batch regression](deliverables/fireworks-tech-graph/runtime/batch-regression.png)

### 展示图有什么用

最终展示不是只摆几张图，而是按用户理解顺序组织的一组架构材料：

- 给产品或评审看：用例图和能力目录能说明“这个 Skill 能做什么”。
- 给新维护者看：逻辑图和开发图能说明“系统怎么分块，代码怎么维护”。
- 给工程排障看：运行图能说明“出图、导出、校验和回归测试怎么串起来”。
- 给后续文档用：PNG 预览图已经合入 `docs/deliverables/fireworks-tech-graph/`。

## Case：dynamo-main

`dynamo-main` 是另一个完整运行过的案例。它分析的是一个推理服务相关仓库，重点展示低延迟推理、分离式推理、KV cache 路由、长上下文卸载、SLA 自动扩缩等能力。

这个案例更适合看复杂工程系统：它不是文档型 Skill，而是有推理入口、调度、缓存、运行时恢复等真实系统链路。

### 用户能力

![dynamo-main use case view](deliverables/dynamo-main/use-case/use-case-view.png)

![dynamo-main use case catalog view](deliverables/dynamo-main/use-case/use-case-catalog-view.png)

### 系统职责

![dynamo-main logic view](deliverables/dynamo-main/logic/logic-view.png)

### 代码维护视角

![dynamo-main development view](deliverables/dynamo-main/development/development-view.png)

### 运行路径

共享缓存启动：

![dynamo-main runtime shared cache startup](deliverables/dynamo-main/runtime/shared-cache-startup.png)

ModelExpress 启动：

![dynamo-main runtime ModelExpress startup](deliverables/dynamo-main/runtime/modelexpress-startup.png)

Checkpoint 热恢复：

![dynamo-main runtime checkpoint recovery](deliverables/dynamo-main/runtime/checkpoint-recovery.png)

展示图目录：`docs/deliverables/dynamo-main/`

## 当前缺口

现在能展示的是历史运行产物，不是标准化 forward-test case。也就是说：

- 仓库里还没有 `forward-tests/` 目录。
- 没有找到独立的 case prompt、输入清单和 judge rubric。
- 所以目前无法逐个列出“哪些标准 case 没跑过”。

如果后续补上标准 case，这个页面应该按每个 case 展示：case 是什么、输入是什么、prompt 是什么、输出效果如何、有没有 judge 结论。
