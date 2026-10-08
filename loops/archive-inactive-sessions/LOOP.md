# 全项目非活跃会话归档 Loop

本 Loop 用于定期归档 Codex 当前登记的本地项目中，最后活跃时间超过指定天数的可识别会话。默认阈值为 7 天。

## 运行边界

- 归档范围来自 Codex `list_projects` 返回的全部本地项目路径；不根据当前工作目录猜测项目。
- 只归档 `scan_inactive_sessions.py` 输出且 `addressable=true` 的线程 ID。
- 置顶会话永不自动归档，也不得为了归档而取消置顶。置顶状态以 `list_threads` 返回的完整 `pinnedThreads` 为准；无法可靠读取置顶状态时必须停止归档，不能按“未置顶”处理。
- 仅存在本地 rollout 文件、没有线程索引实体的记录只统计和报告，不直接删除或修改文件、SQLite 或 rollout 内容。
- 不处理工具返回的 `projectId` 为空或不在本轮项目清单中的聊天，不删除聊天，不删除项目文件。扫描器依据登记的项目路径提供 `projectId`；归档前仍须通过工具复核。
- 归档操作必须通过 Codex 的 `set_thread_archived(threadId, hostId="local", archived=true)` 完成。
- 单条失败不得阻断其余会话；最终报告成功数、失败数、按项目分布和本地不可归档数。
- 归档后抽样调用 `read_thread`、`list_threads(limit=50)` 和 `list_archived_threads` 复核；活动列表最多返回 50 条，缺席本身不能证明归档成功。归档状态可能异步收敛，不能把一次读取失败当作数据删除。

## 每轮步骤

1. 读取根 [AGENTS.md](../../AGENTS.md)，建立本轮 `.tmp/runs/<run-id>/` 工作根目录。不得写入凭据。
2. 调用 Codex `list_projects`，将返回的本地项目数组保存为：

   ```text
   <work-root>/loop-archive-inactive-sessions/projects.json
   ```

   写入前必须先用 Python 创建目录，避免包含中文的 Windows 路径因 shell quoting 导致写入失败：

   ```powershell
   python -c "from pathlib import Path; Path(r'<work-root>\\loop-archive-inactive-sessions').mkdir(parents=True, exist_ok=True)"
   ```

   文件至少包含每个项目的 `label`、`projectId` 和 `path`；建议保留 `projectKind`、`hostId`。支持直接保存数组或 `{"projects": [...]}`，使用 UTF-8（允许 BOM）。必须确认工具 `isError=false` 且返回完整项目清单；真实空数组可作为零项目运行，接口错误或清单缺失不能代替空数组。Windows 命令中的完整路径均使用双引号包住；不要把 JSON 文本插入 PowerShell 双引号命令，优先使用文件写入工具。

3. 运行只读扫描：

   ```powershell
   python -B loops/archive-inactive-sessions/scan_inactive_sessions.py `
     --projects-file "<work-root>/loop-archive-inactive-sessions/projects.json" `
     --output-dir "<work-root>/loop-archive-inactive-sessions" `
     --inactive-days 7
   ```

   脚本按北京时间 UTC+08:00 计算截止时间，扫描本机 Codex session rollout 的元数据和尾部时间戳，并只读查询本地线程目录与线程状态。默认使用 `CODEX_HOME`，未设置时使用用户目录下 `.codex`；`--codex-home` 仅用于指定其他运行环境或隔离测试。rollout 中优先使用 `payload.id`，`session_id` 可能是父会话，不能据此合并子线程。没有 rollout 的 SQLite history 线程从本地目录补充；最后活跃时间取 rollout、目录及线程状态时间的最大值，已归档线程直接排除。它生成：

   - `candidates.json`：可归档线程及本地不可归档记录
   - `candidates.csv`：便于复核的明细
   - `summary.json`：总数和按项目统计

   必须确认扫描进程退出码为 0，再检查三个输出均存在且 JSON 可解析，`generated_at` 属于本轮执行、候选数组长度与统计一致。失败时停止归档并保留日志；不要读取同一目录残留的旧候选。零候选也要生成 `archive-result.json`，记录成功 0、失败 0 和 `no_candidates`。
4. 归档前先调用一次 `list_threads(limit=50)`，确认 `isError=false`、本地主机可用，并把返回的完整 `pinnedThreads` 保存到 `<work-root>/loop-archive-inactive-sessions/pinned-threads.json`。`pinnedThreads` 独立于普通活动列表的 50 条上限；只提取 `kind="codex"` 且 `hostId="local"` 的置顶线程 ID 用于保护。若工具调用失败、本地主机不可用、响应缺少 `pinnedThreads` 或无法解析，停止本轮全部归档并报告 `pinned_state_unavailable`。
5. 逐个检查 `candidates.json` 中 `addressable=true` 且 `eligible=true` 的 ID。候选只要出现在 `pinnedThreads` 中，就在 `archive-result.json` 记录 `skipped=true`、`skip_reason="pinned"`，不得调用 `set_thread_archived`。对其他候选先调用 `read_thread` 核对 `cwd` 和最新 `updatedAt`，再用 `list_threads(limit=50)` 核对 `projectId`、`hostId` 和状态。只归档可确认属于本轮项目、仍超过截止时间、没有运行中且未置顶的会话；字段缺失、项目为空、更新时间已变或样本未出现在完整可见范围时，记录跳过或无法复核，不强行归档。目录数据库内部的 `project_id` 可能为空，不能代替工具返回的项目归属。
   对通过复核的候选，在调用归档接口前必须再次刷新 `list_threads(limit=50)` 并重新检查完整 `pinnedThreads`，避免扫描期间用户刚刚置顶的会话被归档。刷新失败或置顶状态不可确认时，停止后续归档；候选已变为置顶时按 `skip_reason="pinned"` 跳过。只有二次检查仍未置顶，才调用 `set_thread_archived(threadId, hostId="local", archived=true)`。检查 `isError` 和返回的 `archived=true`，不能只把一次 tool call 返回当成功。每次调用或跳过后立即保存 ID、项目、尝试次数、返回结果、跳过原因和错误到 `archive-result.json`；单条失败继续处理后续会话。仅对瞬态失败有限重试最多 2 次，每次重试先重新复核状态、阈值和置顶状态；已经确认归档的不再重试。
6. 从成功列表抽取最多 3 个不同项目的会话，调用 `read_thread` 复核是否仍可按 ID 识别；调用 `list_threads(limit=50)` 检查这些 ID 已不在活动和置顶列表。再用 `list_archived_threads(source="codex", hostId="local")` 查找正面的归档记录，必要时按 `nextCursor` 翻页。对因置顶跳过的会话，抽样确认其仍出现在 `pinnedThreads`，并确认 `archive-result.json` 中没有对应的归档调用。若异步状态未收敛，最多再检查 2 次；仍无法确认则报告“工具归档成功，复核未确认”。复跑只读扫描检查成功 ID 不再出现在候选；置顶跳过项仍作为候选出现是预期行为，不得当作归档失败或再次尝试归档。不要把本地文件删除当作归档成功。
7. 最终报告必须包含截止时间（北京时间）、扫描项目数、rollout 文件数、独立会话数、符合阈值数、成功归档数、失败数、跳过数、因置顶跳过数及其按项目分布、复核状态、本地不可归档数、已归档排除数和按项目分布。不同目录可以同名，按 `projectId` 区分，零候选项目也保留统计。

## 安全约束

- 先扫描后归档；不得把扫描结果缺失当作零候选。
- 不直接编辑 `state_5.sqlite`、`codex-dev.db`、`thread_history_1.sqlite` 或 `.jsonl` 文件来模拟归档。
- 如果 Codex 线程接口不可用，保留扫描结果并报告失败，不执行替代性文件清理。
- 不得取消置顶、移动置顶会话或调用归档接口试探其状态；置顶检查必须失败关闭（fail closed）。
- 索引缺失、数据库查询失败或 rollout 无法解析时，扫描器非零退出；不得把错误解释为零候选或本地不可归档记录。
- 已归档会话可能仍暂留在本地目录中；重复运行必须读取线程状态的 `archived` 并排除，而不能只依赖活动目录中是否有该 ID。
