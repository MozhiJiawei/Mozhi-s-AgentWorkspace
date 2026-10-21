# PR 前 Excel 人工审阅

本规则固定 CCN Loop 的审阅载体。每轮生成新的 Excel，不把历史批次的 `.xlsx` 当作待填模板，也不把私有任务信息纳入仓库。

## 表头和输入

`审阅表` 一行一个任务，保留以下列，不增加分类原因或长篇分析：

| 列 | 表头 | 来源／填写者 |
| --- | --- | --- |
| A | API 编号 | 本轮队列 `row_number` |
| B | API 任务编号 | 本轮队列 `task_id`，映射归档的唯一键 |
| C | API 任务主题 | 原始 `content` 第一行；完整正文留在批次 manifest |
| D | API 任务信息源（URL） | 原始 `url`，可点击 |
| E | API 指定分类 | 原始 `category`；null 显示“未指定（自动分类）” |
| F | AI 当前分类 | 实际归档目录相对于 `ccn-report` 的父目录路径（一级／二级）；不读取 README 分类声明 |
| G | 交付件目录（本地） | 实际归档目录绝对路径，可点击 |
| H | 目录内容 | 实际目录下一层文件及子目录名称，逐项换行；子目录以 `/` 结尾 |
| I | 人工一级分类（下拉） | 人类填写，未改类时留空 |
| J | 人工二级分类（联动） | 只列 I 所选一级的子项 |
| K | 分类选择检查 | 联动检查结果，不代替批准 |

I／J 均留空表示保留 AI 分类。只选一级表示申请一级直归，主 agent 必须按分类总则核实综述资格并更新 README，不得把未理解的内容直接归一级。更换一级后旧二级不会自动清空；不匹配会标红，读取器也会拒绝。普通专题必须选择二级。

批次末尾提供“批次结论”（待审核／通过／修改后再审）、审核人和审核日期。分类留空不等于审核通过，AI 不得代填这些批准信息。人工审阅重点为文件真实性、完整性以及分类结果。

Excel 仅保留 `审阅表` 和支持联动下拉的 `分类枚举`，不生成交付件证据页签。文件路径、字节数、SHA-256 和检查结果仅保留在本地 manifest 中。存在检查和 ZIP／页数检查不等于视觉验收；主 agent 仍须检查最终 HTML 离线打开、PPT 渲染和适用 QA，不能把旧候选版本校验当作最终文件校验。`分类枚举` 每次从 `ccn-report/classification/categories.json` 生成，不硬编码分类数量。

## 生成

先运行 LOOP 第 4 步的交付件校验和归档门禁。生成前按 Spreadsheets skill 读取 API 文档、加载 bundled Node/Python/node_modules 路径，按该 skill 运行 artifact-operation marker；不要改依赖目录或向仓库安装 npm 依赖。

所有输入为本地文件，不查询 API、不创建 PR、不修改归档。以 `pending.json` 精确映射全部任务；目录旧日期不影响任务覆盖。README 用于任务编号映射和交付件链接校验，分类只取实际目录结构，README 缺少或存在不同分类声明不影响分类提取。生成器拒绝缺失／重复映射、未注册目录分类、空文件、LFS 指针以及损坏／非单页 PPTX。

```powershell
$reviewDir = Join-Path $loopRoot 'review-01'
& '<bundled-node>' loops/ccn-brief-report/scripts/build_review_workbook.mjs `
  --tasks "$loopRoot/pending.json" `
  --ccn-root ccn-report `
  --work-root "$workRoot" `
  --review-dir "$reviewDir" `
  --node-modules '<bundled-node_modules>' `
  --python '<bundled-python>'
```

生成 `review.xlsx`、`manifest.json`、本地链接索引、公式扫描记录和两个工作表的 PNG 预览。检查预览后在聊天中提供 Excel 的本地文件入口，等待人类审核；仅口头“先继续”、未填写批准、或无人回复，都不算通过。人类若明确在聊天批准，可由主 agent 记录这次明确批准及其对应的文件版本，再填写审核信息，不能自行推断批准。

生成器拒绝覆盖非空审阅目录。失败重试、修订及恢复沿用同一工作根目录，换用 `review-02` 等新版本目录，不覆盖人类已填文件。

## 读取与提交前检查

人类保存 Excel 后，读取同一文件；如人类另存为其他文件，显式传 `--workbook <绝对路径>`。

```powershell
& '<bundled-python>' loops/ccn-brief-report/scripts/review_workbook.py read `
  --work-root "$workRoot" --review-dir "$reviewDir"
```

读取器核对批次标识、原始 A–H 列、任务覆盖、分类枚举、分类组合、API 分类约束、任务快照及正式文件哈希。它不依赖 Excel 缓存的检查公式，不执行移动或 API 写入。

- 批次结论不是“通过”、审核人／日期为空、文件被修改、组合非法或指定分类冲突：失败并停止提交。冲突不能通过修改本地 API 原值绕过；先请人类解决调用方约束。
- `decisions.json` 的 `status=classification_changes_requested`：仅表示修订计划。主 agent 根据 `task_id` 安全迁移目录，更新 README 分类及链接；先确认目标目录无冲突，不覆盖已有报告。一级直归须有符合总则的 README 说明。
- 调整之后重新运行交付校验及归档门禁，生成新 Excel 并重新取得人工批准。旧审批不能用于修改后的文件。
- `status=approved`：当前快照无人类改类请求；结合主 agent 已完成的最终交付验收，才可进入 LOOP 第 5 步。实际提交前重新执行 `read`，以最新输出为准；不能沿用历史 `decisions.json`。

源文件、任务或分类规则变化时都需要新审阅版本。Excel 和中间证据保留在本轮工作根目录，不能归档到 `ccn-report`，不得把 API Key 或其他凭据写入文件。生成和读取不是 Git 提交、推送、发布、邮件发送或 API 修改授权。
