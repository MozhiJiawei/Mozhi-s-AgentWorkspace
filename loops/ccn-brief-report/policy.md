# CCN 快报 Loop 角色策略

本文件只定义角色责任、交接信息和决策边界。报告内容与归档实现由对应 skill 和子仓规则决定。

子 Agent 的启动与工作目录约束引用根 [AGENTS.md](../../AGENTS.md)；下方模板负责传递本任务所需的具体上下文。

## 主 agent

主 agent 对一轮任务的生命周期负责：

- 按固定 prompt 模板为每个任务启动独立子 agent，只替换占位符。
- 处理子 agent 上报的 HITL；答案必须能从任务目标、来源证据和 skill gate 推导，决定与理由写入任务临时目录。
- 在 Source Understanding HTML 验收通过后，向原报告子 agent 发送消息，要求其根据 `skills/create-single-page-tech-report/SKILL.md` 完成一页 PPT 制作。
- 验收子agent的HTML与PPTX交付件，并按 `LOOP.md` 完成本地归档。
- 根据任务主题和历史归档确定人类可读、可区分的主题短名。优先使用官方产品名、论文系统名、项目名或公认缩写，必要时增加场景或方法消歧词。
- 归档时把正式 HTML 与 PPTX 重命名为相同 basename 的 `<主题短名>.html` 和 `<主题短名>.pptx`，同步更新 README，并在提交和 API 回传前运行 `validate_deliverables.py`。主题短名不得使用通用交付形态、任务编号、批次日期或其他仅对单批任务有效的信息。

## 报告子 agent

### 报告子 Agent Prompt 模板

主 agent 启动每个报告子 agent 时，必须逐字使用以下模板，只替换占位符：

```text
请先读取 <absolute-workspace-root>/AGENTS.md，再根据 <content> + <source> 做一次PPT深度研究。当前工作根目录：<absolute-work-root>，你独占的输出目录：<absolute-task-workspace>。任务指定分类（JSON 值）：<category-json>。先读取 <absolute-workspace-root>/ccn-report/classification/README.md 及候选板块细则，并遵循 <absolute-workspace-root>/loops/ccn-brief-report/LOOP.md 的“可选分类约束”：null 时自动判断；指定一级时在该一级内判断；指定二级时严格遵循。记录分类依据和判断差异。
```

- `<content>`：任务 API 返回的主题与要点。
- `<source>`：任务 API 返回的来源 URL。
- `<category-json>`：任务 API 返回的 `category` 原值序列化为 JSON；未指定填 `null`，不得填空字符串或省略该输入。
- `<absolute-workspace-root>`：主工作区根目录的绝对路径。
- `<absolute-work-root>`：主 agent 按根 `AGENTS.md` 选定的本次工作根目录，与 CLI 的 `--work-root` 一致。
- `<absolute-task-workspace>`：`<absolute-work-root>/loop-ccn-brief-report/<task-id>/` 的绝对路径。
- 任务编号、热点编号和周期由主 agent 保留并在归档时写入正式元信息，不通过扩写子 agent prompt 传递。
- 子 agent 在 `.tmp/` 中使用的 `source_understanding_review.html`、`single_page_tech_report.pptx` 等临时文件名不受正式交付件命名规则约束；主题短名选择和正式重命名由主 agent 在归档阶段负责，不修改固定 prompt 模板。

### HITL 代理

- 主 agent 是本 Loop 中唯一能回答 HITL 的角色。
- 主 agent 应预期报告子 agent 在完整流程中主动询问两次 HITL；除纠错或失败恢复外，不应等待第三个常规 HITL。

#### 第一次 HITL：确认信息源

- 报告子 agent 提交信息源候选并询问是否批准时，表示来源准备完成，但报告生成尚未完成；主 agent 不得把这次询问当作子任务结束。
- 主 agent 必须审核把关信息源质量，优先选用适用于当前任务的原始论文、官方 GitHub 代码仓库、官方 Blog 或项目页等一手来源，避免采用二次加工的新闻稿替代原始证据；不要求每个任务同时具备所有类型的一手来源。
- 如果首次候选不满足要求，主 agent 应明确指出缺失的一手来源或证据问题，并要求报告子 agent 重选；满足要求后由主 agent 明确批准，报告子 agent 继续解析和生成报告。
- 不做对比分析报告；忽略报告子 agent 提供的“参考对照信息源”，只围绕批准的一手来源进行正向分析。

#### 第二次 HITL：确认报告是否 OK

- 报告子 agent 完成 Source Understanding HTML、截图导出和独立视觉 QA 后，会询问报告是否 OK；这次询问是 HTML 阶段的交付信号。
- 主 agent 收到该信号后，应直接检查正式 HTML、截图和 `visual-qa.md`。
- 验收通过时，主 agent 向原报告子 agent 发送消息，要求其根据 `skills/create-single-page-tech-report/SKILL.md` 完成一页 PPT 制作；报告子 agent 完成 PPT 后再交回最终结果，无需增加第三个常规 HITL。
- 验收不通过时，主 agent 才向原报告子 agent 返回具体修改项；子 agent 修订后再次提交“报告是否 OK”，新的询问替代上一次结束信号。
- 任务的可选 `category` 原样透传给报告子 agent；指定分类为归档约束，不自行改类。未指定时按 `ccn-report/classification/README.md` 分级加载并判断；细节见 LOOP.md“可选分类约束”。
