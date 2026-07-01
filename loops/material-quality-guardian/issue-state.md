# GitHub Issue 状态协议

本文件定义资料质量守护者如何使用 GitHub Issue 记录资料刷新问题。

更新 Issue 状态时，必须使用 `loops/material-quality-guardian/issue_db.py`。不要手写 Issue markdown；如果脚本不可用，应先修复脚本或停止并报告。

## 核心规则

- Loop 每轮只做两件事：读取历史 Issue 状态；结合本次扫描发现刷新问题。
- Issue 中长期保留的问题状态只有两个：`待处理`、`已忽略`。
- Loop 只新增或刷新 `待处理` 问题。
- `已关闭` 是临时过渡状态；Loop 读取到后应使用 `issue_db.py delete` 从 Issue 中清理。
- `已忽略` 由人类或其他修复 Agent 通过 `issue_db.py status` 更新，用于明确抑制无需继续关注的问题。
- Loop 不启动修复，也不把问题自动改成 `已忽略`。
- Loop 不回复 Issue，不追加评论；Issue body 是唯一状态面。
- 所有 finding 新增、刷新、忽略和删除都必须通过 `issue_db.py` 完成。
- Issue body 中 marker 外的状态协议必须通过 `issue_db.py sync-protocol` 同步。

## Issue Body 结构

Issue body 应包含一段状态协议和一段问题列表。其他 Agent 可以按这个协议修改问题状态。

```markdown
# Material Quality Guardian

## 状态协议

- `待处理`: 当前仍需要关注或处理的问题。
- `已忽略`: 人类或其他修复 Agent 确认不需要继续处理、但需要保留抑制记录的问题。
- `严重级别`: `P0` / `P1` / `P2`，表示修复优先级；严重级别不替代状态。
- 每个 finding 必须包含 `问题描述`、`页面链接` 和 `代码根因`：问题描述给人类快速判断，页面链接用于打开有问题的资料页，代码根因承载路径、脚本输出、HTTP 状态、指纹等技术细节。
- 已完成的 finding 必须通过 `python loops/material-quality-guardian/issue_db.py delete <id>` 从 Issue 中移除。
- 所有 finding 状态变更必须通过 `python loops/material-quality-guardian/issue_db.py status ...` 或 `delete` 写回 Issue body。
- Guardian Loop 每轮通过 `python loops/material-quality-guardian/issue_db.py list` 读取历史 Issue 状态，并通过 `upsert` 新增或刷新 `待处理` 问题。
- Guardian Loop 不负责修复，也不负责把问题改成 `已忽略`；读取到 `已关闭` finding 时应清理删除。
- Guardian Loop 不回复 Issue，不追加评论；Issue body 是唯一状态面。
- 人类或其他修复 Agent 修复完成后必须用 `issue_db.py delete` 删除问题；确认无需处理时用 `issue_db.py status` 标记为 `已忽略` 并填写 `更新人`、`更新时间`、`处理结论`。
- 不要手写 Issue markdown，也不要通过 Issue 评论表达状态变更；如果脚本不可用，应先修复脚本或停止并报告。

<!-- guardian-findings:start -->
## 问题列表

### MQG-docs-example-missing-source-note

- 状态: 待处理
- 严重级别: P2
- 目标: docs/example.md
- 页面链接: http://docs.haohaoxiaoyu.top:8888/example
- 问题描述: 示例页面提到了外部资料，但读者无法直接判断该资料从哪里核验。
- 代码根因: `docs/example.md` 引用了外部来源，但没有维护对应的来源说明或可访问链接。
- 最近发现: 2026-06-30
- 证据: docs/example.md 引用了外部来源，但没有说明去哪里核验该来源。
- 处理建议: 请确认这个文档是否需要补充来源说明。
<!-- guardian-findings:end -->
```

Guardian 只能通过 `issue_db.py upsert/status/delete` 重写 `guardian-findings` marker 内的问题列表，不应手写 marker 内容。marker 外的状态协议只能通过 `issue_db.py sync-protocol` 更新。

## Finding 字段

每个 finding 至少包含：

- `id`: 稳定 finding ID，写在三级标题中。
- `状态`: `待处理` 或 `已忽略`；`已关闭` 只作为清理前的兼容输入。
- `严重级别`: `P0`、`P1` 或 `P2`。
- `目标`: repo-relative 目标路径或资料标识。
- `页面链接`: 人类可以打开确认问题的资料页面 URL；优先写远端文档站 URL，如果问题只存在于本地或未发布页面，则写本地目标路径并说明未发布。
- `问题描述`: 给人类读的简短问题描述，说明用户在页面上会看到什么异常、为什么需要确认；不要堆脚本输出、指纹、堆栈或实现细节。
- `代码根因`: 给修复 Agent 读的技术根因，承载 repo 路径、manifest 字段、脚本输出、HTTP 状态、指纹差异、fallback 细节等定位信息。
- `最近发现`: Loop 最近一次看到该问题的日期。
- `证据`: 当前证据。
- `处理建议`: 给人类或其他 Agent 的简短处理提示。

## Finding 身份与质量要求

- 每个 finding 必须有稳定 ID，避免同一问题每轮生成新 ID。
- 推荐格式：

```text
MQG-<target-key>-<short-slug>
```

其中 `target-key` 来自 repo-relative path、稳定资料标识或稳定发布目标；`short-slug` 用简短词组描述问题。不要依赖尚未定义的规则编号或证据键体系。
- 默认状态是 `待处理`。
- 默认严重级别是 `P1`；如果不能确定，应先登记为 `P1`，不要为了凑级别降为 `P2`。
- Loop 只新增或刷新 `待处理` finding，不自动改成 `已忽略`；读取到 `已关闭` finding 时应删除。
- 新 finding 必须同时说明代码根因、页面链接和问题描述；缺少任一项时，不应登记为合格 finding。
- 问题描述应面向人类确认：一句话说明页面上的可见问题和影响，不要塞入过多技术细节。
- 页面链接应指向有问题的资料页面，让人类能从 Issue 直接打开页面复核；如果同一问题影响多个页面，优先写最能复现问题的页面，并在证据中补充其他页面。
- 代码根因应面向修复定位：写清楚对应仓库路径、manifest/脚本/发布状态或远端响应中的异常点。
- 新 finding 应优先来自可直接复现的问题，例如路径不存在、manifest 声明文件不存在、入口说明与当前仓库结构明显冲突。
- 对远端发布状态相关 finding，应优先使用可比对的 publish-state 证据，而不是仅凭页面目测判断“像是没发布”。
- 对远端渲染可用性相关 finding，应优先给出真实 URL、HTTP 状态、来源页面和失败类型（404 / fallback / 空白页 / 错误跳转）。

## 严重级别

Guardian 使用三个优先级：

- `P0`: 会让资料入口或核心交付链路整体不可用、明显误导自动化判断，或影响多个 skill / workspace 的发布可信度。典型情况包括：文档站整体发布状态与本地严重漂移、发布验证会把错误页面误判为成功、核心入口页不可打开、关键交付物链接全部失效。
- `P1`: 会让某个 workspace 文档或单个 skill 的重要使用路径出错，用户按文档操作会失败，或文档与实现契约明显不一致。典型情况包括：命令路径不可运行、依赖检查说明与脚本边界不一致、重要 reference 缺失、关键页面或资源链接 fallback。
- `P2`: 局部资料质量问题，不阻断主要使用路径，但会降低可读性、可维护性或后续审查效率。典型情况包括：非核心页面占位、次要示例不完整、说明粒度不足、可改进但不直接导致命令/链接失败的描述漂移。

分级要求：

- 新增 finding 必须带 `严重级别`。
- 严重级别应由当前证据决定，不按发现来源决定；子 agent 只能建议分级，最终以主 agent 登记为准。
- 同一问题如果同时影响远端发布验证和本地文档说明，按更高影响面定级。
- `已忽略` finding 保留原严重级别；重新关注时可以根据新证据调整。

可选字段：

- `首次发现`: 首次发现日期。
- `更新人`: 最近修改状态的人类或 Agent。
- `更新时间`: 最近修改状态的日期。
- `处理结论`: `已忽略` 时的原因说明。

## Loop 更新规则

每轮运行时，Guardian Loop 应：

1. 读取 Issue 中已有 findings。
2. 清理状态为 `已关闭` 的历史 finding。
3. 对本次扫描仍发现的问题：
   - 如果历史中不存在同 ID finding，新增为 `待处理`。
   - 如果历史中存在同 ID finding 且状态是 `待处理`，刷新 `最近发现`、`证据` 和 `处理建议`。
   - 如果历史中存在同 ID finding 且状态是 `已忽略`，保留该状态，不自动重开。
4. 对本次扫描没有发现的问题：
   - 不自动删除 `待处理` 或 `已忽略` finding。
   - 保留原状态，等待人类或其他修复 Agent 判断。

建议命令：

```powershell
python loops/material-quality-guardian/issue_db.py list
python loops/material-quality-guardian/issue_db.py upsert --id MQG-docs-example-missing-source-note --severity P2 --target docs/example.md --page-url "http://docs.haohaoxiaoyu.top:8888/example" --problem "示例页面提到了外部资料，但读者无法直接判断该资料从哪里核验。" --root-cause "docs/example.md 引用了外部来源，但没有维护对应的来源说明或可访问链接。" --evidence "..." --note "..."
python loops/material-quality-guardian/issue_db.py sync-protocol
```

## 人类和修复 Agent 更新规则

人类或其他修复 Agent 必须通过脚本修改 finding 的状态：

- 修复完成后，用 `issue_db.py delete <id>` 从 Issue 中删除该 finding。
- 确认无需处理时，用 `issue_db.py status <id> 已忽略`，并写明 `更新人`、`更新时间` 和 `处理结论`。
- 如果需要重新关注一个已忽略的问题，用 `issue_db.py status <id> 待处理`，并按需再用 `upsert` 更新证据和处理建议。
- 不要手写 Issue markdown，不要通过 Issue 评论表达状态变更。

建议命令：

```powershell
python loops/material-quality-guardian/issue_db.py delete MQG-docs-example-missing-source-note
python loops/material-quality-guardian/issue_db.py status MQG-ccn-report-legacy-material 已忽略 --updated-by MozhiJiawei --resolution "历史样例，无需继续刷新。"
```

`delete` 用于移除已经处理完成或误建的记录；Guardian Loop 读取到 `已关闭` finding 时也应调用 `delete` 清理。

示例：

```markdown
### MQG-docs-example-missing-source-note

- 状态: 已关闭
- 严重级别: P2
- 目标: docs/example.md
- 页面链接: http://docs.haohaoxiaoyu.top:8888/example
- 问题描述: 示例页面提到了外部资料，但读者无法直接判断该资料从哪里核验。
- 代码根因: `docs/example.md` 引用了外部来源，但没有维护对应的来源说明或可访问链接。
- 最近发现: 2026-06-30
- 证据: docs/example.md 引用了外部来源，但没有说明去哪里核验该来源。
- 处理建议: 请确认这个文档是否需要补充来源说明。
- 更新人: repair-agent
- 更新时间: 2026-06-30
- 处理结论: 已在 docs/example.md 中补充来源说明。
```
