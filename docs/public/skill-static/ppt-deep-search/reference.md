# 能力展示

`ppt-deep-search` 的作用不是直接画 PPT，而是在做 PPT 之前，把“材料很多、观点不稳、证据容易说过头”的问题先梳理清楚。它会和用户一起确认读者、判断口径、故事线和证据边界，最后交给下游 PPT 制作环节一份可直接使用的内容简报。

这页展示的是几组真实演示案例。每个案例都按用户能理解的方式说明：

- 用户给了什么材料和任务
- 协作过程中确认了哪些关键判断
- 最后交付了什么
- 研究理解页面长什么样
- 完整 Markdown 简报在哪里阅读

## 展示方式

在线文档最适合直接展示 Markdown 和图片。因此这里采用两种形式：

- **内容简报**：直接链接到 Markdown 文件，文档系统可以继续解析和展示。
- **研究理解网页**：用截图做预览，并提供完整 HTML 链接。HTML 是否能在文档站内直接打开取决于主仓文档系统的静态资源策略；截图加链接是更稳的展示方式。

## 一次协作怎么发生

典型流程是：

1. 先确认读者是谁，以及希望读者改变什么判断。
2. 研究来源材料，必要时生成一页可审阅的 HTML 研究理解报告。
3. 让用户确认“我是否理解对了材料、证据和边界”。
4. 再确认顶层结论、页数、目录和每页观点。
5. 最后输出两个文件：给 PPT 制作使用的 `ppt_content_brief.md`，以及给审计和复查使用的 `research_audit.md`。

## 演示案例总览

| 案例 | 用户任务 | 协作结果 | 可读交付件 |
| --- | --- | --- | --- |
| Aegaeon GPU Pooling | 把一篇 LLM serving / GPU pooling 论文整理成决策型 PPT 内容简报 | 已完成，结论是“先评估，再承诺收益” | [内容简报](showcase/aegaeon-gpu-pooling/ppt_content_brief.md) / [证据审计](showcase/aegaeon-gpu-pooling/research_audit.md) / [研究理解网页](showcase/aegaeon-gpu-pooling/review/source_understanding_review.html) |
| RTX Spark Agent PC | 基于 NVIDIA/Microsoft 官方网页材料，判断 RTX Spark 是否应被看作本地 personal-agent 平台 | 已完成，中途修正过网页正文污染和路径问题 | [内容简报](showcase/rtx-spark-agent-pc/ppt_content_brief.md) / [证据审计](showcase/rtx-spark-agent-pc/research_audit.md) / [研究理解网页](showcase/rtx-spark-agent-pc/review/source_understanding_review.html) |
| Stochastic KV Routing | 把 KV cache 路由论文整理成是否值得进入 serving 实验的技术判断 | 已完成，结论是“先复测，再谈上线” | [内容简报](showcase/stochastic-kv-routing/ppt_content_brief.md) / [证据审计](showcase/stochastic-kv-routing/research_audit.md) / [研究理解网页](showcase/stochastic-kv-routing/review/source_understanding_review.html) |
| TiDAR Hybrid Decoding | 把 diffusion/autoregression 混合解码论文整理成复现实验判断 | 已完成，定位为 controlled-replication candidate | [内容简报](showcase/tidar-hybrid-decoding/ppt_content_brief.md) / [证据审计](showcase/tidar-hybrid-decoding/research_audit.md) / [研究理解网页](showcase/tidar-hybrid-decoding/review/source_understanding_review.html) |
| Goal-Oriented RAG Memory | 把 agentic memory / RAG memory 论文整理成 PPT 内容简报 | 暂无可展示运行记录 | 暂无 |

## Aegaeon GPU Pooling

**背景**

用户给的是一篇系统论文，主题是面向模型市场的 GPU pooling。普通总结很容易只复述“GPU 省了 82%”，但 PPT 决策简报需要回答更实际的问题：这个结果能不能迁移到自己的 serving 场景？哪些证据是生产信号，哪些只是论文或 beta 部署条件下的观察？

**过程**

协作中先确认目标读者和用途，再审阅 source-understanding 页面。通过后继续确认顶层结论、页数、目录、Page 4-7 的页面观点和最终硬约束。整个过程把 `82% GPU saving`、`1,192 -> 213 GPU`、SLO/capacity curves 和 beta deployment 范围分开处理，避免把来源信号说成无限制收益承诺。

**结果**

最终内容简报把 Aegaeon 表达成“先评估，再承诺收益”的架构评估候选，而不是上线建议。

[阅读 Aegaeon 内容简报](showcase/aegaeon-gpu-pooling/ppt_content_brief.md)

[查看 Aegaeon 证据审计](showcase/aegaeon-gpu-pooling/research_audit.md)

[打开完整研究理解网页](showcase/aegaeon-gpu-pooling/review/source_understanding_review.html)

![Aegaeon 研究理解网页预览](assets/forward-tests/aegaeon-gpu-pooling-hitl/source-review.png)

## RTX Spark Agent PC

**背景**

用户给的是多篇 NVIDIA / Microsoft 官方网页和媒体语境，问题不是“RTX Spark 参数有多强”，而是它是否应该被技术架构负责人理解为本地 personal-agent 平台。这个案例还要求区分官方措辞和中文媒体转述，不能把“Agent 原生电脑 / 老黄重新发明 PC”当成官方产品名。

**过程**

协作先确认读者是技术架构 / AI engineering leader。研究阶段抓取网页证据包，生成研究理解网页。初版网页正文混入了推荐、分享等页面 chrome，被要求修正；修正后才继续确认 SCQA、summary、目录、Page 4-6 观点层和最终约束。

**结果**

最终内容简报把 RTX Spark 放进“本地 personal-agent stack”的平台组合里评估：硬件、Windows trust layer、OpenShell policy/runtime、CUDA/RTX 生态需要一起看；同时明确“Agent 原生电脑”只是中文转述，不替代官方措辞。

[阅读 RTX Spark 内容简报](showcase/rtx-spark-agent-pc/ppt_content_brief.md)

[查看 RTX Spark 证据审计](showcase/rtx-spark-agent-pc/research_audit.md)

[打开完整研究理解网页](showcase/rtx-spark-agent-pc/review/source_understanding_review.html)

![RTX Spark 研究理解网页预览](assets/forward-tests/rtx-spark-agent-pc-web-evidence-hitl/source-review.png)

## Stochastic KV Routing

**背景**

用户给的是一篇 KV cache 方向论文。直接做 PPT 很容易把它讲成“又一种 KV 压缩方法”。真正需要判断的是：它是否值得进入 LLM serving 的受控复测？它补的是哪条技术路线的缺口？哪些实验信号足够强，哪些上线条件还没证明？

**过程**

协作先确认受众和用途，然后生成研究理解网页，明确它讨论的是 depth-wise KV sharing，而不是替代 token eviction、KV quantization 或 GQA/MQA。之后逐步确认 SCQA、页数、目录、每页观点和最终约束。

**结果**

最终内容简报形成的顶层判断是“先复测，再谈上线”。它把 Table 4/5 的 capacity 与 batch-scaling 证据作为复测理由，同时把 QA retention、single-GPU measurements、training cost 和 local serving metrics 作为上线前验证门。

[阅读 Stochastic KV Routing 内容简报](showcase/stochastic-kv-routing/ppt_content_brief.md)

[查看 Stochastic KV Routing 证据审计](showcase/stochastic-kv-routing/research_audit.md)

[打开完整研究理解网页](showcase/stochastic-kv-routing/review/source_understanding_review.html)

![Stochastic KV Routing 研究理解网页预览](assets/forward-tests/stochastic-kv-routing-hitl/source-review.png)

## TiDAR Hybrid Decoding

**背景**

用户给的是 TiDAR 论文，主题是 diffusion 和 autoregression 的混合解码。这里的风险是把论文中的吞吐提升直接讲成部署收益，而忽略实验条件、batch 设置、硬件条件和 serving 集成成本。

**过程**

协作先确认读者和用途，再审阅 source understanding。研究过程中区分 free-token-slot motivation、single-forward hybrid diffusion/AR architecture、structured attention masks、quality-throughput evidence 和 baseline comparison。后续再确认 SCQA、页数、目录和 Page 4-7 的页面观点。

**结果**

最终内容简报把 TiDAR 定位为 tracking / controlled-replication candidate，而不是 deployment recommendation。`4.71x` / `5.91x` 被限定为论文条件下、`batch=1` / `single H100` 的 relative AR throughput speedups，custom kernels、long context 和 scheduler integration 被保留为复现门。

[阅读 TiDAR 内容简报](showcase/tidar-hybrid-decoding/ppt_content_brief.md)

[查看 TiDAR 证据审计](showcase/tidar-hybrid-decoding/research_audit.md)

[打开完整研究理解网页](showcase/tidar-hybrid-decoding/review/source_understanding_review.html)

![TiDAR 研究理解网页预览](assets/forward-tests/tidar-hitl/source-review.png)

## 尚未展示的案例

`Goal-Oriented Reasoning for RAG-based Memory in Conversational Agentic LLM Systems` 已经有演示 case 定义，但当前仓库本地没有对应的最新运行产物。因此这页只展示它的任务背景，不展示结果截图或交付件。

等该案例产生完整运行记录后，应补充：

- 内容简报 Markdown
- 证据审计 Markdown
- 研究理解 HTML
- 研究理解页面预览图

## 素材来源说明

这些演示素材已经整理为可发布副本：适合阅读的交付件位于 `docs/showcase/`，研究理解网页的预览图位于 `docs/assets/forward-tests/`。
