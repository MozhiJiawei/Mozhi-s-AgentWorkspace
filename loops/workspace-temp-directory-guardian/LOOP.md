# Workspace 临时目录守护 Loop

本 Loop 检查 Git 可见目录和 `.tmp/` 工作区结构。Git 目录扫描以当前 `.gitignore` 为准，不检查其哈希或判定其是否合规。它只报告问题，不修改忽略规则或清理目录。

## 规范

### Git 目录检查

- 每轮直接执行目录检查，使用当前 Git 忽略规则。
- 对根仓及已初始化子仓，只使用 Git 的 untracked 结果发现额外目录，不根据目录名称另行猜测；ignored 目录不报告为 Git 目录问题。
- untracked 目录需要确认是应纳入版本控制的正式内容，还是错误放置的临时产物。
- 同一父目录下的嵌套问题只报告最外层目录。

### `.tmp/` 结构

- `.tmp/` 根目录只允许 `README.md`、`runs/` 和 `retained/`。
- `runs/` 与 `retained/` 必须存在；两者根部只允许 `.gitkeep` 和工作目录，不允许散落文件。
- run root 必须使用 `YYYYMMDD-HHMMSS-<short-name>` 格式，并包含有效日期和时间。
- retained work root 使用用户指定的非空目录名。
- 若 run root 的 `<short-name>` 与 retained work root 同名，报告同一工作同时使用两种模式。
- 工作目录内部结构由具体任务决定，不重复检查。

Loop 无法从文件系统判断 retained 是否确由用户授权，也无法证明不同名称的目录属于同一工作；这两项保留为 Agent 执行约束。

## 每轮步骤

1. 在 Workspace 根目录运行：

   ```powershell
   python -B loops/workspace-temp-directory-guardian/check_temp_directories.py --workspace .
   ```

2. 根据退出码报告结果：
   - `0`：Git 可见目录和 `.tmp/` 结构均合规。
   - `1`：报告每项问题及判定依据。
   - `2`：扫描未完整执行；报告错误，不得宣称 Workspace 合规。

3. 不自动修改 `.gitignore`，也不清理或移动目录；修复必须由用户另行授权。
