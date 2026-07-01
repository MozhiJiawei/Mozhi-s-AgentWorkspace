# 资料质量守护策略

本文件定义资料质量守护 Loop 的执行契约：看什么、谁来做、怎么委派，以及至少要做哪些检查。

只基于当前仓库已经存在的文件、`docs/`、各 skill 的 `docs/`、发布构建输入以及生成材料判断问题。不要因为缺少尚未定义的元数据、登记表或治理制度而判定违规。

## 守护范围

关注这些资料：

| 类型 | 路径 | 关注点 | 分工 |
| --- | --- | --- | --- |
| workspace 仓文档 | `README.md`<br>`AGENTS.md`<br>`docs/` | 工作区入口、指令约束、工作区文档是否仍准确；同时检查与 skills 仓文档不重复的内容 | `workspace docs` 子 agent |
| Skills 仓文档 | `skills/*/docs/`<br>`skills/*/docs.manifest.yml` | skill 文档入口、依赖说明、使用说明与 manifest 声明是否仍能和对应内容互相印证 | 每个已注册 skill 各自一个子 agent |
| 远端文档站规则检查 | `http://docs.haohaoxiaoyu.top:8888/` | 远端站点与本地源码是否一致，以及远端骨架渲染是否正确 | 主 agent |

## 角色分工

- 主 agent 职责：
  - 决定本轮审查单元，委派子agnet执行审查。
  - 为每个子 agent 提供明确边界、目标路径、目标 skill 和当前已忽略的问题。
  - 汇总子 agent 结果，并按 `issue-state.md` 定义的结构整理 findings 后通过 `issue_db.py upsert/status` 写回 Issue。
  - 执行远端文档站规则检查，包括一致性检查和骨架渲染正确性检查。
- 子 agent 职责：
  - 只负责被分配的审查单元，不扩张到别的 skill 或全仓。
  - 先读本地文档，再读相关实现证据，再验证远端真实渲染结果。
  - 返回结构化结论：发现了什么、证据是什么、建议主 agent 如何登记。

## 子 Agent Prompt 模板

主 agent 在委派 skill 文档审查单元时，至少应传达以下信息：

```text
你负责本轮资料质量守护中的一个审查单元：<unit-name>。

目标范围：
- 本地文档：<docs paths>
- 相关实现证据：<implementation paths>
- 远端站点：http://docs.haohaoxiaoyu.top:8888/

你的任务：
1. 先阅读本地文档，理解这个单元对外承诺了什么。
2. 再阅读必要的实现证据，判断文档里哪些链接、页面、交付物或子报告是高价值检查点。
3. 打开远端真实渲染页面，验证：
   - 首页是否可打开；
   - 导航页是否可打开；
   - 文档正文里的关键内容链接是否可打开；
   - 是否出现 404、HTML fallback、空白页或错误跳转。
4. 需要时运行通用自动化检查补充证据。
5. 只返回这个单元的 findings 候选，不要替主 agent 改 Issue。

当前已忽略的问题列表：
* <finding-1>
* <finding-2>

返回格式：
- unit: <unit-name>
- status: ok | findings
- evidence:
  - <bullet>
- findings:
  - id_hint: <short-slug>
    severity: P0 | P1 | P2
    target: <path-or-url>
    evidence: <one paragraph>
    note: <one sentence>
```

## 通用自动化检查

- 通用自动化检查只负责提供基础证据，不替代子 agent 判断。
- 当前共享检查入口是：
  - `python loops/material-quality-guardian/qa/run.py --include-remote --output-root .tmp/loops/material-quality-guardian`
- 主 agent 或子 agent 可以按需调用这些入口，但不需要在 prompt 里解释脚本内部原理。
- 这些入口的 CLI 输出应直接给出模型需要的关键信息，例如：
  - 本次检查的目标；
  - `ok` / `drift` / `broken-links` / `missing` 等状态；
  - 关键证据；
  - 建议是否应登记 finding。
- 仓库内可复用工具只提供审计能力，不负责模拟或替代子 agent 生命周期。

## 忽略范围

以下路径不参与资料质量判断：

- `.git/`
- `.tmp/`
- `node_modules/`
- `skills/*/__pycache__/`
- `skills/*/node_modules/`
- `skills/*/package-lock.json`
