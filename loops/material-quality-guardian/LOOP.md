# 资料质量守护者 Loop

本 Loop 用于在每轮运行时审视工作区资料状态，并把资料刷新问题登记到指定 GitHub Issue 中。

当前 active state Issue：[MozhiJiawei/Mozhi-s-AgentWorkspace#12](https://github.com/MozhiJiawei/Mozhi-s-AgentWorkspace/issues/12)。

## 目标

- 发现当前仓库中可以直接复现的资料问题。
- 读取 GitHub Issue 中已有 finding 状态。
- 结合本次扫描发现新增或刷新 `待处理` 问题。
- 清理已完成的历史 finding；Issue 中只长期保留 `待处理` 和确需抑制的 `已忽略` 问题。

## 运行边界

- 本 Loop 不自动修改正式资料、代码、文档内容或 skill 内容。
- 本 Loop 必须通过 `issue_db.py` 重写 GitHub Issue 中由 guardian 管理的 findings 区块。
- 本 Loop 只新增或刷新 `待处理` finding，不自动改成 `已关闭` 或 `已忽略`；如果读取到 `已关闭` finding，应通过 `issue_db.py delete` 从 Issue 中移除。
- 本 Loop 不回复 Issue，不追加评论；所有状态都写在 Issue body 中。
- 本 Loop 和修复 Agent 都不要手写 Issue markdown；状态协议通过 `issue_db.py sync-protocol` 同步，finding 状态通过 `issue_db.py status` 更新。
- 本 Loop 的单轮临时产物必须写入 `.tmp/loops/material-quality-guardian/`。

## 每轮步骤

1. 调用 `python loops/material-quality-guardian/issue_db.py list` 读取 GitHub Issue 当前 findings。
2. 调用 `python loops/material-quality-guardian/qa/run.py --include-remote --output-root .tmp/loops/material-quality-guardian` 执行统一资料 QA，并把输出作为本轮基础证据。
3. 按 `policy.md` 定义的审查执行模型完成本轮资料审查，并按 `issue-state.md` 定义的状态、严重级别和字段格式形成本轮 findings。
4. Agent 结合历史 Issue 状态和本轮 findings 登记刷新问题：
   - 历史中存在状态为 `已关闭` 的 finding，先用 `issue_db.py delete` 删除；不要继续作为子 agent 前置输入。
   - 历史中不存在同 ID finding，则用 `issue_db.py upsert` 新增为 `待处理`。
   - 历史中存在同 ID finding 且状态是 `待处理`，用 `issue_db.py upsert` 刷新证据和 `最近发现`。
   - 历史中存在同 ID finding 且状态是 `已忽略`，保留该状态，不自动重开。
   - 本次未扫描到的历史 `待处理` 或 `已忽略` finding，保留原状态，不自动删除或关闭。
5. 如果状态协议需要更新，调用 `python loops/material-quality-guardian/issue_db.py sync-protocol`，不要手写 Issue body。
