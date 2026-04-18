# AGENTS.md

本文件只保存 skills 的暴露说明和使用约束，不保存仓库说明。

当任务涉及修改仓库代码、调整目录结构、更新工程约定或处理非 skill 内容时，agent 应先阅读 `README.md`。

## `.tmp/` Usage Principle

- `.tmp/` 是 agent 在本工作区内处理所有临时产物时唯一的工作根目录。
- 调用任何 skill 时产生的中间稿、日志、草图、导出文件和阶段性结果，都必须写入 `.tmp/` 下。
- 具体子目录命名和拼接方式，按对应 skill 自身说明执行。
- 若 skill 文档中给出了临时产物目录规则，应将该规则视为相对于 `.tmp/` 的子路径规则，而不是写到 skill 仓库或其他位置。
- 除非用户明确要求生成正式、可追踪的仓库内容，否则不要把这类产物直接写到仓库正式位置。

## Pre-Commit Gates

- agent 每次提交代码前，都必须运行统一门禁入口：`python scripts/pre_commit_gate.py`
- 只要任一门禁失败，就不要提交，先修复失败项。
- 具体门禁项由 `scripts/pre_commit_gate.py` 统一编排；不要绕过这个入口单独挑选运行。

## Registered Skills

### `skills/architecture_4-1`

- 加载路径：`skills/architecture_4-1/SKILL.md`
- skill 名称：`generate-3plus1-diagrams`
- 主要用途：分析目标仓库并生成 3+1 / 4+1 架构视图的可编辑 `.drawio` 图，以及对应的导出预览和校验结果

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求分析某个代码仓库的架构
- 用户要求生成架构图、模块图、组件关系图或 draw.io 图
- 用户明确提到 3+1、4+1、逻辑视图、开发视图、运行时视图、用例视图
- 用户希望基于代码仓库梳理模块边界、组件关系、运行路径或用户用例结构

当任务只是修改业务代码、修文档、修脚本、维护仓库骨架，且不涉及架构视图产出时，不应加载这个 skill。

使用这个 skill 时：

- 先读取 `skills/architecture_4-1/SKILL.md`
- 若任务会产生中间稿、日志、草图或阶段性结果，必须以 `.tmp/` 为工作根目录，并按该 skill 的目录约定拼接子路径
- 若用户明确要求分析当前仓库，也应把本仓库视为目标仓库，但临时架构产物仍必须落在 `.tmp/` 下

### `skills/ppt_gen_wqt`

- 加载路径：`skills/ppt_gen_wqt/SKILL.md`
- skill 名称：`tech-report-ppt-safe-layout`
- 主要用途：生成或修改技术汇报类 PPT，并在交付前执行版式安全检查，避免文字重叠、裁切和超出边界

当任务满足以下任一条件时，agent 应加载并使用这个 skill：

- 用户要求创建、生成、编写、重做或导出 PPT / PowerPoint
- 用户要求修改、润色、重排、续写或修复已有 PPT
- 用户要求制作论文汇报、技术汇报、方法介绍、benchmark 评审或技术 deck
- 用户明确要求检查 PPT 布局安全性、文字是否溢出、是否裁切、是否重叠

当任务只是整理普通文档、写纯文本大纲、修改代码或处理与 PPT 无关的内容时，不应加载这个 skill。

使用这个 skill 时：

- 先读取 `skills/ppt_gen_wqt/SKILL.md`
- 若任务会产生中间稿、图片、图表素材、生成脚本、检查结果或阶段性 PPT，必须以 `.tmp/` 为工作根目录，并按该 skill 的目录约定拼接子路径
- 生成或修改 PPT 后，应按该 skill 的要求运行相应检查脚本，再交付结果
