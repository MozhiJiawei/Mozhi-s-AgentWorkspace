# CCN 快报 Loop 角色策略

本文件只定义角色责任、交接信息和决策边界。报告内容与归档实现由对应 skill 和子仓规则决定。

## 主 agent

主 agent 对一轮任务的生命周期负责：

- 按固定 prompt 模板为每个任务启动独立子 agent，只替换占位符。
- 处理子 agent 上报的 HITL；答案必须能从任务目标、来源证据和 skill gate 推导，决定与理由写入任务临时目录。
- 验收已审批的 Source Understanding 交付，并按 `LOOP.md` 完成本地归档。

## 报告子 agent

### 报告子 Agent Prompt 模板

主 agent 启动每个报告子 agent 时，必须逐字使用以下模板，只替换三个占位符，不允许添加任何额外说明：

```text
请你根据 <content> + <source> 做一次PPT深度研究，工作区：<absolute-task-workspace>
```

- `<content>`：任务 API 返回的主题与要点。
- `<source>`：任务 API 返回的来源 URL。
- `<absolute-task-workspace>`：`.tmp/loops/ccn-brief-report/<task-id>/` 的绝对路径。
- 任务编号、热点编号和周期由主 agent 保留并在归档时写入正式元信息，不通过扩写子 agent prompt 传递。

### HITL 代理

- 主 agent 是本 Loop 中唯一能回答 HITL 的角色。
- 主 agent 应预期报告子 agent 在完整流程中主动询问两次 HITL；除纠错或失败恢复外，不应等待第三个常规 HITL。

#### 第一次 HITL：确认信息源

- 报告子 agent 提交信息源候选并询问是否批准时，表示来源准备完成，但报告生成尚未完成；主 agent 不得把这次询问当作子任务结束。
- 主 agent 必须审核把关信息源质量，优先选用适用于当前任务的原始论文、官方 GitHub 代码仓库、官方 Blog 或项目页等一手来源，避免采用二次加工的新闻稿替代原始证据；不要求每个任务同时具备所有类型的一手来源。
- 如果首次候选不满足要求，主 agent 应明确指出缺失的一手来源或证据问题，并要求报告子 agent 重选；满足要求后由主 agent 明确批准，报告子 agent 继续解析和生成报告。
- 不做对比分析报告；忽略报告子 agent 提供的“参考对照信息源”，只围绕批准的一手来源进行正向分析。

#### 第二次 HITL：确认报告是否 OK

- 报告子 agent 完成 Source Understanding HTML、截图导出和独立视觉 QA 后，会询问报告是否 OK；这次询问是报告生成阶段的最终交付信号。
- 主 agent 收到该信号后，应直接检查正式 HTML、截图和 `visual-qa.md`，并进入验收与归档流程，不再等待报告子 agent 额外发送一次“已完成”消息。
- 验收通过时，主 agent 将这次询问视为报告子任务结束，并按 `LOOP.md` 继续归档、门禁、PR 合入和任务结果回传。
- 验收不通过时，主 agent 才向原报告子 agent 返回具体修改项；子 agent 修订后再次提交“报告是否 OK”，新的询问替代上一次结束信号。
