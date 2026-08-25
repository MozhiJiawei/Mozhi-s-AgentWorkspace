# CCN 快报归档与交付 Loop

本 Loop 是快报任务的主编排入口。它定义执行顺序和角色交接，不复制 workspace skills 或 `ccn-report` 的实现规范。

## 目标与完成条件

每轮从 CCN 任务 API 读取全部待处理任务，为尚未归档的任务生成正式报告。报告先通过 `ppt-deep-search` 产出并验收 Source Understanding HTML，再通过 `ccn-report` 的 HTML 归档验收；只有 HTML 通过验收后，主 agent 才使用 `create-single-page-tech-report` 将该 HTML 总结为一页可编辑 PPTX。主 agent 将同时包含 HTML 和 PPTX 的正式报告包归档到当前工作区的 `ccn-report/`，再通过 Pull Request 合入 GitHub 归档仓库并上传任务完成记录。

完成条件：
  - 每条记录都要让报告子 agent 输出并通过审批 gate：`source_understanding_review.html`。
  - 每条记录的 HTML 都先通过 `ccn-report` 的 SingleFile、README、来源和目录规范验收，再进入 PPT 生成阶段。
  - 每条记录都由主 agent 使用 `create-single-page-tech-report` 基于已验收 HTML 生成严格一页、无动画、可编辑的 `single_page_tech_report.pptx`，并通过该 skill 的结构校验和人工视觉复核。
  - 每个正式报告目录都同时包含 `source_understanding_review.html`、`single_page_tech_report.pptx` 和 `README.md`；PPT 预览、校验日志和阶段性文件不得归档。
  - 所有报告都由主 agent 归档到 `ccn-report`，并提 PR 合入。
  - 每条记录都通过 API 回复结果；重新查询任务 API 后没有 pending 记录。

## API Key 首次配置

首次运行若出现“缺少 CCN API Key”，按以下优先级配置：

1. 环境变量 `CCN_API_KEY`。
2. 仓库外私有配置文件；默认位置是用户主目录下的 `.ccn-brief-report/client.json`：
   - `%USERPROFILE%\.ccn-brief-report\client.json`

私有配置文件格式：

```json
{
  "api_key": "<CCN_API_KEY>"
}
```

如需使用其他私有文件位置，设置 `CCN_BRIEF_TASK_API_CONFIG` 指向该文件。环境变量 `CCN_API_KEY` 的优先级高于私有配置文件。

API Key 禁止写入仓库、命令输出、日志、截图、任务产物或 Pull Request；配置文件必须位于仓库外。

## ccn-report 报告 README 规范

每个归档报告目录都必须包含 `README.md`。主 agent 在提交 `ccn-report` Pull Request 前必须逐项验收以下四部分；缺少任一部分或内容不符合要求时，不得提交。

### 1. 一句话总结

- 使用一句独立、完整、可直接引用的话回答“这个技术是什么”，具体要求与 `ccn-report/AGENTS.md` 的 README SMART Summary 完全一致。

### 2. 任务信息

原样记录本轮从 CCN API 获取的任务字段，不改写任务正文：

- 序号：`row_number`
- 任务编号：`task_id`
- 热点编号：`hotspot_id`
- 周期：`period`
- 任务正文：`content`
- 任务来源：`url`，必须写成可点击的 Markdown 链接。

### 3. 交付件说明

- 逐项列出该报告目录内实际归档的正式交付件，并使用相对 Markdown 链接指向文件。
- 每项说明交付形态及用途，例如 dependency-free SingleFile HTML、可编辑 PPTX 或可演示 PPTX。
- 不得列入未归档的临时草稿、截图、缓存、日志、QA 中间记录或 `.tmp/` 文件。

### 4. 引用信息源说明

- 列出制作报告时实际参考的原始信息源，包括原始论文、官方 GitHub 仓库、官方项目页或原始 Blog；每项必须使用可点击的 Markdown 链接。
- 每项简要说明该来源支撑了报告中的什么内容或结论。
- 只列实际使用的来源，不把搜索结果页、临时 source package、本地路径或未使用的候选来源写入 README。
- 优先列一手来源；任务 URL 如果是二手报道，可以作为任务背景保留在“任务信息”，但不能替代本节对应的原始论文、官方代码或官方 Blog。

README 模板：

```markdown
# <报告标题>

## 一句话总结

<符合 ccn-report SMART 要求的一句话技术总结。>

## 任务信息

- 序号：<row_number>
- 任务编号：<task_id>
- 热点编号：<hotspot_id>
- 周期：<period>
- 任务正文：<content，原样保留>
- 任务来源：[<来源标题或 URL>](<url>)

## 交付件说明

- [source_understanding_review.html](./source_understanding_review.html)：dependency-free SingleFile Source Understanding HTML，可离线打开。
- [single_page_tech_report.pptx](./single_page_tech_report.pptx)：基于已验收 HTML 总结的一页式可编辑技术洞察 PPTX。

## 引用信息源说明

- [<原始论文标题>](<论文 URL>)：用于支撑<实验、方法或指标>。
- [<官方项目或代码仓库>](<GitHub URL>)：用于支撑<实现、版本、许可或使用方式>。
- [<官方 Blog 或项目页>](<URL>)：用于支撑<发布时间、产品定位或官方说明>。
```

该模板表示最终归档状态。HTML 阶段验收时，README“交付件说明”只能列出已经存在的 `source_understanding_review.html`；`single_page_tech_report.pptx` 实际生成并通过验收后，再补入对应条目，禁止提前声明不存在的交付件。

## HTML 验收后生成 PPT

PPT 是已验收 HTML 的下游摘要，不是并行生成物，也不能替代 HTML。必须遵循以下顺序：

1. 报告子 agent 完成 `ppt-deep-search`，主 agent 批准第二次 HITL，并确认正式 `source_understanding_review.html`、截图和 `visual-qa.md` 通过该 skill 的审批 gate。
2. 主 agent 将 HTML 导出为 dependency-free SingleFile，并按 `ccn-report/AGENTS.md`、`ccn-report/README.md` 和本文件的 README 规范完成 HTML 阶段验收。此时只确认 HTML、来源、SMART 一句话总结、目录和 README 信息满足归档要求，不创建 PR，也不把任务视为完成。
3. HTML 阶段验收通过后，主 agent 读取 `skills/create-single-page-tech-report/SKILL.md`，以正式报告目录中的 `source_understanding_review.html` 为内容基线，在 `.tmp/create-single-page-tech-report/<task-id>/` 中生成 PPT 草稿、预览和校验日志。PPT 不得新增 HTML 中没有依据的事实、数据或结论；若发现 HTML 本身存在证据问题，应退回 HTML 验收阶段修正后再重新生成 PPT。
4. 将最终文件命名为 `single_page_tech_report.pptx`，并从 workspace 根目录运行：

   ```powershell
   python skills/create-single-page-tech-report/scripts/validate_single_page_report.py `
     .tmp/create-single-page-tech-report/<task-id>/single_page_tech_report.pptx
   ```

5. 结构校验通过后，主 agent 还必须检查渲染预览中的标题语义、证据边界、字体字号、溢出、遮挡、图表清晰度和底部洞察启示。只有机器校验与人工复核都通过，才把 `single_page_tech_report.pptx` 复制到正式报告目录。
6. 正式归档只保留 `source_understanding_review.html`、`single_page_tech_report.pptx` 和 `README.md`。将 PPT 加入 README“交付件说明”，再次运行 `ccn-report` 仓库门禁；预览图片、`visual-qa.md`、校验日志、草稿和缓存继续留在 `.tmp/`，不得归档。

`resume_from=delivery` 的任务不得重复启动 `ppt-deep-search` 报告子 agent。若正式目录已有通过验收的 HTML 但缺少 PPTX，只执行本节第 3–6 步；若 HTML 尚未通过验收，则先完成第 2 步，再生成 PPT。

## 每轮步骤

1. 获取本轮本地锁；无论成功、失败或中断，退出前都必须释放：

   ```powershell
   python loops/ccn-brief-report/local_state.py lock acquire
   # 本轮结束时在 finally/清理阶段执行：
   python loops/ccn-brief-report/local_state.py lock release
   ```

2. 使用脚本读取 API pending 并生成工作队列，不由 agent 手工判断本地状态：

   ```powershell
   python loops/ccn-brief-report/task_api.py fetch
   python loops/ccn-brief-report/local_state.py filter `
     --tasks .tmp/loops/ccn-brief-report/tasks.json `
     --output .tmp/loops/ccn-brief-report/pending.json `
     --ccn-root ccn-report
   ```

   - API 返回的 pending 永远保留在工作队列中，本地 README 或本地 `archived` 记录不能把它过滤掉。
   - `resume_from=generation`：本地没有报告，从报告生成开始。
   - `resume_from=delivery`：本地已有报告，跳过重复的深度研究；根据正式目录实际状态，从 HTML 阶段验收、PPT 补齐、仓库门禁、远端合入确认或结果回传继续。
   - 无效 API 记录写入 `.tmp/loops/ccn-brief-report/rejected-tasks.json`，其余合法任务继续处理；主 agent 在本轮总结中报告 rejected，但不让单条坏记录阻断整轮。
3. 对 `resume_from=generation` 的任务按 `policy.md` 启动报告子 agent；HTML 验收标准是完成 `ppt-deep-search` 及其审批 gate，并发上限读取 `config.json`。`resume_from=delivery` 的任务不得重复启动报告子 agent。
4. 按 `ccn-report/AGENTS.md`、`ccn-report/README.md` 及本文件的“ccn-report 报告 README 规范”完成 HTML 阶段归档验收；README 必须完整保留任务信息、HTML 交付件及带链接的实际引用来源。此阶段不得创建报告 PR。
5. 严格按本文件“HTML 验收后生成 PPT”执行 `create-single-page-tech-report`：基于已验收 HTML 生成、渲染并校验 `single_page_tech_report.pptx`。`resume_from=delivery` 若已有合格 HTML 但缺 PPT，只补做本步骤，不重跑深度研究。
6. 将通过验收的 PPTX 加入同一正式报告目录和 README“交付件说明”，确认目录最终只包含 HTML、PPTX 和 README，再运行 `ccn-report` 仓库门禁。
7. 在 `ccn-report` 中只提交本轮报告相关文件，推送分支并创建 Pull Request；持续跟进 CI、必需检查和评审意见，修复后重新验证，直到 PR 已实际合入默认分支并确认远端报告目录同时存在 HTML 和 PPTX。不能把“PR 已创建”“CI 通过”或“可合并”当作完成。
8. 合入确认后，只使用 `task_api.py complete` 完成结果回传、服务端对账和本地状态落盘，不由 agent 手工拼 POST 或单独调用 `local_state.py mark`：

   ```powershell
   python loops/ccn-brief-report/task_api.py complete `
     --task-id <task_id> `
     --artifact-url <GitHub报告目录直达URL> `
     --report-path <本地报告目录>
   ```

   `complete` 使用稳定幂等键；POST 超时后会查询任务最新结果，只有服务端状态为 `completed` 且 URL 完全一致时，才自动把本地状态写为 `archived`。

   结果内容规范：
   - 结果内容只传 `outcome` 和 `artifact_urls`，不传 `summary` 或 `metadata`。
   - `artifact_urls` 只包含一个 URL：报告在 GitHub 默认分支上的目录直达地址，格式为 `<ccn_report_repository_url>/tree/main/<报告相对目录>`。
   - `<报告相对目录>` 使用 `/` 分隔；URL 必须能直接打开已合入的报告目录，不传仓库根地址、本地路径或临时预览地址。
   - URL 的路径统一使用可读的中文 IRI 形式。客户端和服务端都必须把等价的 percent-encoded UTF-8 路径规范化为中文后，再计算幂等键和对账；服务端 API 统一返回中文形式，但数据库保留原始提交值，不迁移或重写历史数据。ASCII 保留字符（例如 `%20`、`%2F`）不得被误解码。
9. 重新运行 `task_api.py fetch`；只有 API pending 为 0、rejected 已报告、本地没有未对账任务，且本轮合入的每个远端报告目录都同时存在 HTML 和 PPTX 时，本轮完成。最后释放本地锁。

结果记录示例：

```json
{
  "outcome": "completed",
  "artifact_urls": [
    "https://github.com/MozhiJiawei/ccn-report/tree/main/开源软件分析/Example/20260805-example-source-understanding-codex"
  ]
}
```
