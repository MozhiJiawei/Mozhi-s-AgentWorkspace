# 核心概念

本页解释工作区里反复出现的核心词汇。

## Workspace

Workspace 指这个主仓。它提供共享协议、文档发布、依赖复核和提交前门禁。

可以把 workspace 理解成大厅：它帮助读者找到正确房间，但不会替每个房间重写自己的说明。

## Skills

Skills 是挂载在 `skills/` 下的一组独立能力，通常以 Git submodule 形式接入。

每个 skill 拥有自己的 `SKILL.md`、文档、脚本、示例、依赖和验证逻辑。Workspace 通过 Skills 帮助读者回答：

- 当前有哪些 skills？
- 哪个 skill 适合我的任务？
- 权威说明在哪里？

它不应该复制完整的 skill 使用文档。

## 文档服务器

文档服务器是统一发布面。

它通过一个 VitePress 站点发布主仓工作区说明和已注册 skill 文档。服务器可以聚合和路由，但 skill 文档的所属文件仍然留在 skill 子仓。

## 依赖复核

`docs/skill-dependencies.yml` 记录每个 skill 的依赖复核状态。

当可能影响运行依赖的文件变化后，应先复核依赖状态，再刷新对应指纹。

## Pre-Commit Gate

`python scripts/pre_commit_gate.py` 是提交前仓库健康检查的唯一入口。

它会编排注册表检查、文档漂移检查、依赖复核检查、README prompt 示例覆盖检查和相关校验。

## `.tmp/`

`.tmp/runs/<run-id>/` 是默认的一次性工作根目录；`<run-id>` 使用“时间戳 + 简短名称”。同一次工作中的 agents、skills、loops 和插件共享它。

草稿、日志、导出图片、中间 XML、生成 deck 和本地实验都应放在当前工作根目录内。只有用户明确指定某项长期本地工作时，才直接使用 `.tmp/retained/<work-name>/`，并停止为同一工作创建 run；普通 checkpoint 不自动进入 retained。需要正式保存或评审的仓库内容仍应升格到 `.tmp/` 之外。
