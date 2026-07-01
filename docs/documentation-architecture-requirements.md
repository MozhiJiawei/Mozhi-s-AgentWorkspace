# 文档架构需求

本文是 Agent 修改工作区资料时的写作约束。重点不是介绍文档站历史，而是让 Agent 知道：资料写在哪里、四个 skill 页面分别写什么、改完后怎么校验。

## 文档边界

- 主仓负责文档系统、导航、发布、门禁和跨 skill 索引。
- Skill 子仓负责自己的使用说明、示例、限制、排障、依赖说明和架构说明。
- 主仓不要复制 skill 子仓的详细正文；需要发布 skill 内容时，通过 `skills/*/docs.manifest.yml` 同步。
- Skill 子仓不要要求主仓手工改写内部使用细节；应在子仓 `docs/` 中提供可发布资料。

## Skill 文档 Manifest

每个已注册 skill 必须在子仓根目录提供：

```text
docs.manifest.yml
```

manifest 至少要声明：

- `schema_version`
- `name`
- `title`
- `description`
- `entry`
- `nav`

`nav` 必须包含四个固定中文入口：

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

路径可以按 skill 实际文件组织调整，但侧边栏标题必须使用这四个固定名称。`架构概览` 可以指向 `docs/index.md`，也可以指向独立架构页。

## 四个必选页面

| 页面 | 写作目标 | 必须包含 | 失败条件 |
| --- | --- | --- | --- |
| `能力展示` | 证明 skill 能交付什么。 | 真实示例或截图<br>覆盖的能力点<br>可在线打开的交付件、图片、HTML 或报告链接<br>示例来源<br>能力边界 | 只有口号<br>只列本地路径<br>链接返回 HTML fallback<br>用目录结构代替结果展示 |
| `使用方式` | 让用户能直接发起任务，让 Agent 按正确边界执行。 | 可复制 prompt<br>输入、输出、临时目录<br>可运行命令及工作目录<br>完成标准<br>涉及子 agent / checker 时提醒用户允许启动 | 没有 prompt<br>命令目录不对<br>涉及子 agent 但不提醒授权<br>只写“参考 SKILL.md” |
| `依赖说明` | 让 Agent 判断环境是否可运行、缺失时怎么修。 | 外部依赖<br>必需/可选区分<br>`verify_dependencies.py` 调用方式<br>脚本实际检查与不会检查的范围<br>修复方向 | 不列外部依赖<br>夸大自检覆盖范围<br>把仓库文件扫描当依赖检查<br>写入敏感凭据值 |
| `架构概览` | 让用户理解这个 skill 的工作原理和协作边界。 | 逻辑视图：核心概念、输入输出、关键模块和边界<br>运行视图：从用户 prompt 到交付物的主要执行路径<br>开发视图：面向理解原理的目录、脚本和资料分层<br>多 Agent 职责及边界：主 agent、子 agent、checker 或 reviewer 的分工、交接物和禁止事项 | 只有目录树<br>写成完整系统论文<br>只列测试、forward-test 或内部 QA<br>不解释逻辑/运行/开发三类视图<br>multi-agent skill 不说明主/子 agent 分工 |

## Agent 写作流程

1. 读取本文和目标 skill 的 `docs.manifest.yml`。
2. 先读目标 skill 的 `SKILL.md`、manifest 指向的资料页和 `verify_dependencies.py`；只有资料页引用到的 `references/`、脚本或示例产物才继续读取。
3. 按四个必选页面分别补齐内容，不把所有信息塞进一个页面。
4. 运行 `python scripts/sync_skill_docs.py`。
5. 运行 `python scripts/pre_commit_gate.py`。
6. 如果文档指纹漂移，确认资料已复核后运行 `python scripts/check_skill_docs.py --update-fingerprints`，再重新运行 pre-commit gate。
7. 只有用户要求发布验收，或本轮修改涉及远端可访问性时，发布后运行 `python loops/material-quality-guardian/qa/run.py --output-root .tmp/loops/material-quality-guardian`。

## QA 守护

- `scripts/check_skill_docs.py` 检查 skill 文档来源是否复核并刷新指纹。
- `loops/material-quality-guardian/qa/check_docs_skill_surfaces.py` 检查文档站 skill 列表和四个必选导航项。
- `loops/material-quality-guardian/qa/run.py` 在 Loop 中同时检查本地资料和远端发布状态。

Material Quality Guardian 登记资料问题时，finding 必须包含页面链接、面向人类的问题描述和面向修复 Agent 的代码根因。
