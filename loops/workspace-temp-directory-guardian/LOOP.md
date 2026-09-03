# Workspace 临时目录守护 Loop

本 Loop 以自身规范为准，依次检查根 `.gitignore`、Git 可见目录和 `.tmp/` 工作区结构。它只报告问题，不修改忽略规则或清理目录。

## 规范

### `.gitignore`

- `gitignore.sha256` 保存当前已批准根 `.gitignore` 的 SHA-256；Loop 内不复制 `.gitignore` 内容。
- 每轮先比较根 `.gitignore` 的规范化 UTF-8 文本哈希。哈希不一致时提醒用户关注，并跳过后续 Git 目录检查。
- 换行按文本语义统一处理，避免 CRLF/LF 差异误报。
- 当前忽略项的存在理由：Node 依赖目录可重复安装；文档目录由构建和同步脚本生成；Python 目录保存字节码、测试缓存和可再生的打包元数据；`.tmp/` 是正式临时工作区，`.tmp_old/` 是暂时保留的旧工作区。
- 不要为规避目录问题直接修改 `.gitignore` 或哈希。规则确需变化时，先审阅 `.gitignore`，再基于批准后的文件更新哈希。

### Git 目录检查

- 只有根 `.gitignore` 完全符合上述规范后，才执行目录检查，避免重复报告同一配置根因。
- 对根仓及已初始化子仓，只使用 Git 的 untracked 结果发现额外目录，不根据目录名称另行猜测；已批准的 ignored 目录由 `.gitignore` 哈希覆盖。
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
   - `0`：`.gitignore`、Git 可见目录和 `.tmp/` 结构均合规。
   - `1`：报告每项问题；若 `.gitignore` 不合规，说明 Git 目录检查已跳过。
   - `2`：扫描未完整执行；报告错误，不得宣称 Workspace 合规。

3. 不自动修改 `.gitignore`，也不清理或移动目录；修复必须由用户另行授权。
