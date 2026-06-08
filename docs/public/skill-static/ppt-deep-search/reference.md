# 能力展示

`ppt-deep-search` 把论文、网页或材料包转成可直接用于 PPT 生成的内容简报和证据审计，让复杂材料先完成观点对齐，再进入制图和排版。

| 输入 | 输出 | 最关键效果 |
| --- | --- | --- |
| PDF、网页、论文解析包、目标读者和汇报意图 | `ppt_content_brief.md`、`research_audit.md`、研究理解网页 | 先确认观点和证据边界，再生成 PPT |

![Aegaeon 研究理解网页预览](assets/forward-tests/aegaeon-gpu-pooling-hitl/source-review.png)

这张预览展示的是研究理解页面。它证明这个 skill 的核心价值不是“总结材料”，而是先把读者、结论、证据和风险说清楚，避免后续 PPT 把材料讲偏。

## 适合场景

- 材料很多，但顶层观点还不稳。
- 论文或网页证据容易被说过头。
- 做 PPT 前需要先确认读者、故事线和页面观点。
- 需要把研究过程留下审计记录。

## 处理过程

1. 确认读者是谁，以及希望读者改变什么判断。
2. 研究来源材料，必要时生成研究理解网页。
3. 让用户确认材料理解、证据边界和风险。
4. 确认顶层结论、页数、目录和每页观点。
5. 输出内容简报和证据审计，交给 PPT 生成流程使用。

## 交付物

| 交付物 | 用途 |
| --- | --- |
| `ppt_content_brief.md` | 给 PPT 生成 skill 使用 |
| `research_audit.md` | 记录证据、判断和边界 |
| 研究理解网页 | 让用户先审阅材料理解是否正确 |
| 页面预览图 | 在文档站中快速查看研究理解效果 |

## Case：Aegaeon GPU Pooling

### 用户任务

把 LLM serving / GPU pooling 论文整理成决策型 PPT 内容简报，重点判断“是否值得评估”，而不是直接承诺上线收益。

### 输入

- 系统论文材料。
- 决策型 PPT 目标。
- 用户对收益口径和证据边界的要求。

### 输出

- [内容简报](showcase/aegaeon-gpu-pooling/ppt_content_brief.md)
- [证据审计](showcase/aegaeon-gpu-pooling/research_audit.md)
- [研究理解网页](showcase/aegaeon-gpu-pooling/review/source_understanding_review.html)

### 关键效果

![Aegaeon 研究理解网页预览](assets/forward-tests/aegaeon-gpu-pooling-hitl/source-review.png)

这个案例证明系统能把 `82% GPU saving`、`1,192 -> 213 GPU`、SLO/capacity curves 和 beta deployment 范围分开处理，避免把来源信号说成无限制收益承诺。

## Case：RTX Spark Agent PC

### 用户任务

基于 NVIDIA / Microsoft 官方网页材料，判断 RTX Spark 是否应该被理解为本地 personal-agent 平台。

### 输入

- 官方网页和媒体语境。
- 技术架构 / AI engineering leader 读者定位。
- 对官方措辞和中文转述的区分要求。

### 输出

- [内容简报](showcase/rtx-spark-agent-pc/ppt_content_brief.md)
- [证据审计](showcase/rtx-spark-agent-pc/research_audit.md)
- [研究理解网页](showcase/rtx-spark-agent-pc/review/source_understanding_review.html)

### 关键效果

![RTX Spark 研究理解网页预览](assets/forward-tests/rtx-spark-agent-pc-web-evidence-hitl/source-review.png)

这个案例证明系统能处理网页材料污染，区分官方信息、媒体转述和架构判断。

## Case：Stochastic KV Routing

### 用户任务

把 KV cache 路由论文整理成是否值得进入 serving 实验的技术判断。

### 输入

- KV cache 方向论文。
- 受控复测和上线前验证的判断需求。

### 输出

- [内容简报](showcase/stochastic-kv-routing/ppt_content_brief.md)
- [证据审计](showcase/stochastic-kv-routing/research_audit.md)
- [研究理解网页](showcase/stochastic-kv-routing/review/source_understanding_review.html)

### 关键效果

![Stochastic KV Routing 研究理解网页预览](assets/forward-tests/stochastic-kv-routing-hitl/source-review.png)

这个案例证明系统能把 depth-wise KV sharing 与 token eviction、KV quantization、GQA/MQA 等路线区分开，并把结论收束为“先复测，再谈上线”。

## Case：TiDAR Hybrid Decoding

### 用户任务

把 diffusion/autoregression 混合解码论文整理成复现实验判断。

### 输入

- TiDAR 论文和解析材料。
- 对吞吐收益、实验条件和 serving 成本的边界要求。

### 输出

- [内容简报](showcase/tidar-hybrid-decoding/ppt_content_brief.md)
- [证据审计](showcase/tidar-hybrid-decoding/research_audit.md)
- [研究理解网页](showcase/tidar-hybrid-decoding/review/source_understanding_review.html)

### 关键效果

![TiDAR 研究理解网页预览](assets/forward-tests/tidar-hitl/source-review.png)

这个案例证明系统能把论文中的 `4.71x` / `5.91x` 限定在 batch=1、single H100 等实验条件下，保留 custom kernels、long context 和 scheduler integration 等复现门槛。

## 展示覆盖

| Case | 输入 | 输出 | 证明的能力 |
| --- | --- | --- | --- |
| Aegaeon GPU Pooling | 系统论文 | brief、audit、研究理解网页 | 收益口径和生产证据边界 |
| RTX Spark Agent PC | 官方网页材料 | brief、audit、研究理解网页 | 网页证据清洗和官方措辞区分 |
| Stochastic KV Routing | KV cache 论文 | brief、audit、研究理解网页 | 技术路线定位和复测判断 |
| TiDAR Hybrid Decoding | 论文和解析材料 | brief、audit、研究理解网页 | 实验条件约束和复现门识别 |
| Goal-Oriented RAG Memory | case 定义 | 暂无最新运行产物 | 待补展示 |

## 当前缺口

`Goal-Oriented Reasoning for RAG-based Memory in Conversational Agentic LLM Systems` 已有演示 case 定义，但当前仓库本地没有对应的最新运行产物。后续需要补充内容简报、证据审计、研究理解 HTML 和预览图。
