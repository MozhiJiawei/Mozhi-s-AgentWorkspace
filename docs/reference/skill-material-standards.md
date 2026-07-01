# Skill 资料规范

本页定义已注册 skill 子仓对外资料的写作规范。Agent 新增或修改 `skills/*/docs/`、`skills/*/docs.manifest.yml` 时，应先阅读本页，再修改具体 skill 文档。

这些规范关注给人类和 Agent 看的资料质量，不替代 `SKILL.md` 的运行指令，也不替代 `verify_dependencies.py` 的依赖自检。

## 基本原则

- 每个已注册 skill 必须在 `docs.manifest.yml` 中暴露四个资料入口：`能力展示`、`使用方式`、`依赖说明`、`架构概览`。
- 四个入口必须能在文档站侧边栏中看到，并能从远端文档站打开。
- 页面内容应帮助读者判断“这个 skill 能做什么、怎么用、需要什么、内部怎么运转”，不要只列文件名或复制 `SKILL.md`。
- 资料页可以引用 `SKILL.md`、`references/`、脚本、forward-test、示例产物和校验结果，但必须把读者需要的结论写在页面正文里。
- 页面中的内部交付件、示例、报告、图片、HTML 预览和静态资源链接必须真实可打开；不要暴露会落到 VitePress HTML fallback 的假直链。

## `能力展示`

`能力展示` 用来回答：这个 skill 做出来的结果长什么样，能力边界在哪里，哪些交付件可以被读者直接检查。

最低内容：

- 用图、截图、HTML 预览、导出图片、报告片段或真实示例展示 skill 的输出形态。
- 说明这些示例覆盖了哪些能力点，例如研究、抓取、生成、解析、发送、架构建模或质量检查。
- 给出可在线打开的内部交付件链接；如果链接指向图片、HTML、报告或静态资产，远端必须返回真实内容。
- 说明示例的来源和状态，例如 forward-test、最新 showcase、人工样例或真实运行产物。
- 明确能力边界：哪些情况可用，哪些情况只是示例，哪些情况不能代表完整能力。

不合格例子：

- 只有一句“本 skill 支持某能力”，没有示例或可检查产物。
- 页面列了本地文件路径，但远端用户打不开。
- 交付件链接返回 200 HTML fallback，而不是目标图片、HTML 或报告。
- 把实现目录结构当成能力展示，没有说明用户能获得什么结果。

## `使用方式`

`使用方式` 用来回答：用户应该怎样向 Agent 发起任务，Agent 应该怎样执行这个 skill。

最低内容：

- 给出可直接复用的典型 prompt，覆盖主要使用场景。
- 写清楚推荐的工作目录、输入文件、输出目录和临时产物位置。
- 给出关键命令时，必须确认命令能从文档声明的目录运行；如果需要进入 skill 子仓，应明确写出来。
- 说明完成标准，例如应生成哪些文件、应运行哪些校验、结果应写到哪里。
- 如果实现或流程涉及子 agent、并行审查、独立 checker 或 delegated review，典型 prompt 必须明确提醒用户允许启动子 agent。

不合格例子：

- 只有实现说明，没有用户可复制的 prompt。
- 命令默认读者在 skill 子仓内，但文字说可以从主仓根目录运行。
- 涉及子 agent 的流程没有告诉用户需要允许子 agent，导致实际执行被简化。
- 只说“参考 SKILL.md”，没有整理用户入口、输入输出和验收方式。

## `依赖说明`

`依赖说明` 用来回答：运行这个 skill 前，外部环境需要满足什么，如何验证，缺失时怎么处理。

最低内容：

- 列出真实外部依赖，例如 Python 包、Node 包、浏览器运行时、系统工具、命令行工具、外部服务、账号凭据、环境变量或网络访问。
- 区分必需依赖和可选依赖；可选依赖缺失时应说明影响哪些能力。
- 给出依赖自检命令，通常是 `python skills/<skill>/verify_dependencies.py`。
- 说明自检脚本实际检查什么、不会检查什么；不要把内部文件扫描包装成完整外部依赖检查。
- 给出缺失依赖的修复方向，例如安装命令、环境变量名称、服务地址或跳过服务检查的参数。

不合格例子：

- 只说“运行 verify_dependencies.py”，但不列外部依赖。
- 自检脚本只检查 Python 版本，却文档声称已检查浏览器、服务和工具链。
- 把仓库内文件是否存在当成依赖说明主体。
- 涉及凭据时没有说明需要哪些环境变量，或者把敏感值写进文档。

## `架构概览`

`架构概览` 用来回答：这个 skill 内部如何分层、如何执行、哪些组件承担什么职责。

最低内容：

- 给出逻辑视图：核心概念、输入、输出、关键模块和边界。
- 给出运行视图：一次典型任务从用户 prompt 到最终交付的执行路径。
- 给出开发视图：重要目录、脚本、references、测试/forward-test、校验入口如何组织。
- 说明资料与实现的对应关系：哪些文档是入口，哪些脚本是验证，哪些产物是示例。
- 如果涉及 multi-agent、子 agent、独立 checker 或主/子流程协作，必须说明主 agent 和子 agent 的职责边界、交接物和禁止事项。

不合格例子：

- 只有目录树，没有解释运行路径和职责。
- 只描述实现细节，没有告诉读者如何理解输入、输出和边界。
- multi-agent skill 没有说明主 agent 与子 agent 分工。
- 架构页面引用了过期脚本、已删除目录或不可访问交付件。

## Manifest 要求

每个 skill 子仓的 `docs.manifest.yml` 应声明四个必选导航项。标题必须使用中文固定名称，路径可以按 skill 实际文件组织决定。

```yaml
entry: docs/index.md
nav:
  - title: 能力展示
    path: docs/reference.md
  - title: 使用方式
    path: docs/usage.md
  - title: 依赖说明
    path: docs/dependencies.md
  - title: 架构概览
    path: docs/index.md
```

`架构概览` 可以指向 `docs/index.md`，也可以指向独立架构页。无论路径如何，页面正文都必须满足本规范中的架构概览要求。

## Agent 写作流程

Agent 修改 skill 资料时应按这个顺序执行：

1. 读取本页和目标 skill 的 `docs.manifest.yml`。
2. 阅读目标 skill 的 `SKILL.md`、`docs/`、必要的 `references/`、脚本和示例产物。
3. 按四个必选页面分别补齐内容，不把所有信息塞进一个页面。
4. 运行 `python scripts/sync_skill_docs.py` 刷新文档站聚合产物。
5. 运行 `python scripts/pre_commit_gate.py`。
6. 如果资料来源变化导致文档指纹漂移，复核后运行 `python scripts/check_skill_docs.py --update-fingerprints`，再重新运行 pre-commit gate。
7. 需要人工检查远端时，发布后运行 `python loops/material-quality-guardian/qa/run.py --output-root .tmp/loops/material-quality-guardian`。

## 与守护 Loop 的关系

Material Quality Guardian 使用本规范作为 skill 资料审查口径。发现问题时，finding 应给出人类可打开的页面链接、面向人类的问题描述，以及面向修复 Agent 的代码根因。
