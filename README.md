# Mozhi's Agent Workspace

这是一个为 Codex agent 设计的工作区骨架，用来集中维护仓库说明、skills 子仓，以及 skills 运行时生成的临时产物。

## 目录结构

```text
.
|-- AGENTS.md
|-- README.md
|-- .gitignore
|-- .tmp/
|   `-- .gitkeep
+-- skills/
    `-- .gitkeep
```

## 仓库约定

- `README.md` 保存仓库说明、目录职责和工程约定。
- 当 agent 需要修改仓库代码、调整目录结构或处理非 skill 内容时，应先阅读 `README.md`。
- `AGENTS.md` 只保存 skills 的暴露说明和使用约束。
- `skills/` 只用于挂载 skill 来源仓，默认采用多个 Git submodule 的组织方式。
- `.tmp/` 用于存放 skill 运行时生成的草稿、日志、调试文件和导出物；这些内容默认不进入版本控制。

## 添加一个 skill submodule

在仓库根目录执行：

```powershell
git submodule add <repo-url> skills/<source-or-skill-name>
git commit -m "Add skill submodule: <source-or-skill-name>"
```

命名建议：

- 目录名使用 skill 来源名或 skill 包名
- 尽量稳定，不随单次任务改名
- 一个来源一个目录，避免把多个无关来源混在同一个子模块路径下

## 更新与同步 submodule

拉取仓库后初始化并同步子模块：

```powershell
git submodule update --init --recursive
```

更新某个已接入 skill：

```powershell
git -C skills/<source-or-skill-name> pull
git add skills/<source-or-skill-name>
git commit -m "Update skill submodule: <source-or-skill-name>"
```

## .tmp/ 使用方式

当 prompt 引导某个 skill 工作时，生成产物应默认写到：

- `.tmp/<skill-name>/`
- `.tmp/<date-task>/`

推荐把这类内容放进 `.tmp/`：

- 中间结果
- 导出文件
- 调试日志
- 草稿与实验性产物

不建议把需要长期保留、需要评审或需要版本追踪的正式内容放进 `.tmp/`。

## Skill Prompt 示例

本节为每个已注册 skill 提供几条可直接复用的 prompt 示例，便于快速触发对应能力。

### `skills/architecture_4-1`

适用场景：分析目标仓库架构，产出 3+1 / 4+1 架构视图、draw.io 图和相关校验结果。

示例 prompt：

- `请你分析目标仓库里的 omni_infer 模块，给出 omniProxy 的用例视图，重点突出加速特性。允许参照SKILL描述使用子agent配合分析。`
- `请基于这个仓库生成 4+1 架构图，只需要逻辑视图和运行时视图，输出 draw.io 文件。允许参照SKILL描述使用子agent配合分析。`
- `请梳理当前仓库的模块边界和关键运行路径，并给我一套可编辑的 3+1 架构图。允许参照SKILL描述使用子agent配合分析。`

### `skills/ppt_gen_wqt`

适用场景：基于论文 PDF 分析并生成或修改技术汇报类 PPT，并在交付前做版式安全检查。

示例 prompt：

- `请根据这篇论文 PDF 分析并生成一份 12 页左右的技术汇报 PPT，风格偏正式。`
- `请基于这篇论文 PDF 提炼方法、实验和结论，并输出一份适合组会汇报的 PPT。`
- `请读取这篇论文 PDF，做一份论文方法介绍的汇报 deck，重点检查标题、正文和图片不要重叠或超出边界。`
