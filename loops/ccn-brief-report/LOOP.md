# CCN 快报归档与交付 Loop

本 Loop 是快报任务的主编排入口。它定义执行顺序和角色交接，不复制 workspace skills 或 `ccn-report` 的实现规范。

## 目标与完成条件

每轮从 CCN 任务 API 读取全部待处理任务，为尚未归档的任务生成正式报告，由主 agent 将通过验收的报告归档到当前工作区的 `ccn-report/`，再通过 Pull Request 合入 GitHub 归档仓库并上传任务完成记录。

完成条件：
  - 每条记录都要让子agent输出报告：`source_understanding_review.html`。
  - 所有报告都由主agent归档ccn-report，并提PR合入
  - 每条记录都通过API回复结果，通过任务API查询，没有pending的记录

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

## 引用信息源说明

- [<原始论文标题>](<论文 URL>)：用于支撑<实验、方法或指标>。
- [<官方项目或代码仓库>](<GitHub URL>)：用于支撑<实现、版本、许可或使用方式>。
- [<官方 Blog 或项目页>](<URL>)：用于支撑<发布时间、产品定位或官方说明>。
```

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
   - `resume_from=delivery`：本地已有报告，跳过重复生成，从门禁、远端合入确认或结果回传继续。
   - 无效 API 记录写入 `.tmp/loops/ccn-brief-report/rejected-tasks.json`，其余合法任务继续处理；主 agent 在本轮总结中报告 rejected，但不让单条坏记录阻断整轮。
3. 对 `resume_from=generation` 的任务按 `policy.md` 启动报告子 agent；验收标准是完成 `ppt-deep-search` 及其审批 gate，并发上限读取 `config.json`。`resume_from=delivery` 的任务不得重复启动报告子 agent。
4. 按 `ccn-report/AGENTS.md`、`ccn-report/README.md` 及本文件的“ccn-report 报告 README 规范”归档验收通过的报告；README 必须完整保留任务信息、列明交付件及带链接的实际引用来源，再通过仓库门禁。
5. 在 `ccn-report` 中只提交本轮报告相关文件，推送分支并创建 Pull Request；持续跟进 CI、必需检查和评审意见，修复后重新验证，直到 PR 已实际合入默认分支并确认远端存在报告目录。不能把“PR 已创建”“CI 通过”或“可合并”当作完成。
6. 合入确认后，只使用 `task_api.py complete` 完成结果回传、服务端对账和本地状态落盘，不由 agent 手工拼 POST 或单独调用 `local_state.py mark`：

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
7. 重新运行 `task_api.py fetch`；只有 API pending 为 0、rejected 已报告且本地没有未对账任务时，本轮完成。最后释放本地锁。

结果记录示例：

```json
{
  "outcome": "completed",
  "artifact_urls": [
    "https://github.com/MozhiJiawei/ccn-report/tree/main/开源软件分析/Example/20260805-example-source-understanding-codex"
  ]
}
```
