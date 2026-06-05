# PPT Content Brief

## Deck Metadata
主题：TiDAR hybrid diffusion-autoregressive decoding 是否值得跟踪复现
目标读者：模型架构 / serving platform leaders
页数口径：7 total PPT pages；Page 1 cover，Page 2 top-level summary，Page 3 contents，Page 4-7 content pages
核心结论：TiDAR 架构有新意，值得进入受控复现；论文报告的 4.71x / 5.91x 是 batch=1/single H100 设置下 relative AR throughput speedup，不等同于我们的 serving 收益
内容来源：TiDAR paper package
关联审计文件：research_audit.md

## Summary Page
页码：Page 2
页面标题：架构有新意，收益待验证
标题说明：TiDAR 把 diffusion pre-draft 放进 AR sampling，但平台收益仍取决于本地 serving 栈
分析总结：
- 架构：structured masks 让验旧草稿与预写新草稿并行
- 实验：8B 平均 T/NFE 8.25，对 AR 报 5.91x speedup
- 假设：free token slots 在高 batch 和长上下文下未证明
正文内容：
- 架构：TiDAR 的核心不是单纯“多生成几个 token”，而是在 single model forward 中把三类 token 放到同一次计算里：prefix tokens 复用已有 KV cache；上一步 drafted tokens 通过 AR sampling / rejection 形成 verifier output；下一步 mask tokens 通过 diffusion 分支提前生成 proposals。这个结构让 diffusion 的并行草稿能力服务于下一步生成，同时让最终输出仍经过 AR 路径约束，适合被定位为 hybrid architecture candidate。
- 架构：Figure 2 展示了上一步草稿、下一步 pre-draft 和 prefix 的并置关系；Figure 3 展示了 training mask 与 decoding mask 如何把 clean tokens 的 causal attention、mask tokens 的 block-bidirectional attention、以及推理期的 reordering / slicing 组织在一起。后续复现不应只跑 checkpoint 指标，还要确认 mask slicing、proposal selection、exact KV cache handling 是否能在本地实现中保持低额外成本。
- 实验：论文报告 TiDAR 1.5B 和 8B 分别以平均 T/NFE 7.45 与 8.25 输出，对应相对同规模 AR baseline 的 4.71x 与 5.91x decoding throughput speedup。Table 2 中 TiDAR Trust Diff 8B 的 generative average 为 65.31%，低于 Qwen3 8B 的 68.09%，但高于 Dream 7B 的 58.74%；Table 3 中 TiDAR 8B 的 likelihood average 为 75.40%，高于 Qwen3 8B 的 74.25%。这些数字支持“值得复现”，但不支持直接写成平台收益。
- 实验：Table 4 是避免误读的关键补充。普通 confidence decoding 在提高 T/NFE 后会明显损失 HumanEval Avg、MBPP Avg 和 GSM8k 表现，而 TiDAR 4/8/16 drafts 在更高 T/NFE 下仍保持较强分数。这说明论文主张不只是“接受更多 token”，而是通过 AR sampling 与 diffusion pre-drafting 的组合维持 quality-throughput tradeoff。
- 假设：Figure 1 的 free token slots profiling 是 serving 价值的前提，不是 serving 价值本身。它说明在 Qwen3-32B、H100、batch size 1、Flash Attention 2 的 profiling 中，部分额外 token slots 可以在 latency 基本不等比例上升的区间内被利用。后续必须在本地 batch 分布、硬件、continuous batching、scheduler、KV 管理、custom kernels 和 long context 条件下重新验证。
- 假设：本 deck 的整体建议是 tracking / controlled replication。读者应先判断 TiDAR 的 single-forward hybrid architecture 是否值得工程复现，再判断论文 quality-throughput signal 是否稳定，最后把 batch、hardware、long context、custom attention kernels、scheduler / serving stack integration 作为复现门槛，而不是把 4.71x / 5.91x 改写成 production QPS、tail latency、GPU utilization 或 cost saving。
参考图片：
- ![Figure 2: TiDAR single-forward architecture](brief-assets/picture_003.png)
- Figure 2 展示 prefix、上一步 drafted tokens、下一步 pre-drafted mask tokens 在同一次 forward 中如何协作。
- ![Figure 4: Efficiency-quality benchmarking](brief-assets/picture_005.png)
- Figure 4 展示 TiDAR 与 AR、EAGLE-3、Block Diffusion 在相对吞吐和任务分数上的关系，适合支撑“值得复现”的顶层判断。
备注：
- 4.71x / 5.91x 必须写成论文设置下 relative AR throughput speedup；不能改写成我们的 serving 收益。

## Table of Contents
01 小标题：先看机制
说明：判断 TiDAR 的 single-forward hybrid architecture 是否真有差异化，而不是普通 multi-token decoding。

02 小标题：再拆证据
说明：把 quality-throughput signal 和 AR / speculative / diffusion baseline 对比分开读，确认论文信号是否足够复现。

03 小标题：最后验假设
说明：把 batch=1、single H100、long context、custom kernels 和 scheduling 写成复现门槛，而不是部署结论。

## Page Content

### Page 4: 差异在同一 forward
所属章节：先看机制
页面标题：差异在同一 forward
标题说明：TiDAR 用 structured masks 同时验旧草稿、预写新草稿，决策点是机制是否值得复现
分析总结：
- 机制：AR sampling 保护输出质量，diffusion pre-draft 占用空闲 token slots
- 复现点：mask slicing、KV cache 和 proposal selection 是实现成本核心
正文内容：
- 机制：TiDAR 的架构判断应从 Figure 2 开始，而不是从“diffusion 比 AR 快”开始。它把 generation step 拆成 prefix tokens、tokens drafted from last step、tokens pre-drafted for next step 三个区域：prefix 复用历史 KV cache；上一步 draft 在当前 forward 内被 AR 路径采样和拒绝；下一步 mask tokens 同时由 diffusion 路径提前形成 proposals。这个设计让系统有机会把 memory-bound 区间里的额外 token slots 变成可用草稿，而最终输出仍经 AR sampling 约束。
- 机制：Figure 3 说明 structured masks 是架构可信度的关键。训练时 clean input tokens 走 causal self-attention，appended mask tokens 在 block 内 bidirectional attention 并看见 prefix；推理时通过预初始化 mask 的 slice 和输入重排，把当前 prefix、旧草稿、新 mask proposals 组织成可复用的 decoding mask。读者应看到：TiDAR 的“hybrid”不是两个模型串起来，而是同一模型内部用不同 attention pattern 同时承载 AR 与 diffusion 角色。
- 复现点：实现成本首先落在 mask slicing / reordering 上。Page 4 应提醒下游 PPT maker 不要把 Figure 3 当成纯概念图；它代表了 推理期 mask 管理、位置重排、prefix 长度变化、block length 选择和 proposal 对齐的实际工程面。复现时如果 mask 处理导致额外 kernel launch、缓存错位或 batch packing 困难，论文中的 free-token-slot 假设可能无法转化为本地收益。
- 复现点：exact KV cache handling 也不是附带细节。Figure 2 中 causally forwarded tokens 的 KV cache 会被保存，若对应 token 被 rejected 后还要处理 evict 或 discard。这个流程影响 serving stack 的状态管理、回滚逻辑、cache allocator、以及 scheduler 对不同 sample 接受长度的处理方式。后续复现应记录 accepted length 分布和 proposal selection 行为，而不仅记录最终 tokens/s。
- 复现点：Page 4 的读者判断是“机制是否值得复现”。如果团队只想验证论文 headline speedup，可能会低估 architecture integration 成本；如果先确认 Figure 2/3 所示机制能在本地 stack 中被干净实现，后续 Page 5 的吞吐和质量数字才有解释意义。此页不需要展开 generic AR / diffusion 背景，只需要把 TiDAR 的结构差异和复现成本讲透。
参考图片：
- ![Figure 2: TiDAR Architecture](brief-assets/picture_003-2.png)
- Figure 2 展示 TiDAR 在 single forward 中同时处理 verifier output 与下一步 proposals 的架构。
- ![Figure 3: TiDAR Attention Masks](brief-assets/picture_004.png)
- Figure 3 展示 training mask 与 decoding mask，说明 structured masks 如何支撑同一模型内的 AR / diffusion 分工。
备注：
- 此页不能把 TiDAR 简化成普通 multi-token prediction；要强调同一 forward 内 AR sampling 与 diffusion pre-drafting 的组合。

### Page 5: 证据够复现，不够上线
所属章节：再拆证据
页面标题：证据够复现，不够上线
标题说明：4.71x/5.91x 是论文 batch=1/single H100 下 relative AR throughput speedup
分析总结：
- 吞吐：1.5B/8B 分别报告 4.71x 与 5.91x，但只证明论文设置
- 质量：Table 2/3 显示接近 AR，Table 4 说明高 T/NFE 未崩
正文内容：
- 吞吐：论文在 abstract、main result 和 conclusion 中报告 TiDAR 1.5B 与 8B 平均 T/NFE 分别为 7.45 和 8.25，并转化为相对同规模 AR baseline 的 4.71x 与 5.91x tokens/s speedup。Page 5 的标题说明必须保留 `batch=1/single H100` 和 `relative AR throughput speedup` 这两个口径，因为这两个数字只说明论文 benchmark 设置下 TiDAR 的 decoding throughput 位置，不能代表我们的 production QPS、TPOT、tail latency 或 GPU cost。
- 吞吐：Figure 4 是 Page 5 的主视觉。它把不同任务分数放在纵轴，把 relative AR throughput speedup 放在横轴，并按 1.5B 与 8B 分组比较 AR、EAGLE-3、Block Diffusion 和 TiDAR。读者应从 Figure 4 得到的判断是：TiDAR 在论文设置中形成了一个值得复测的 quality-throughput frontier；读者不应从 Figure 4 直接得到“上线后吞吐提升 5.91x”的结论。
- 质量：Table 2 支撑 generative quality 没有被吞吐完全牺牲。TiDAR 1.5B 平均 44.03%，高于 Block Diff 1.5B 的 38.41%，也高于 Qwen2.5 1.5B 的 41.64%；TiDAR Trust Diff 8B 平均 65.31%，低于 Qwen3 8B 的 68.09%，但高于 Dream 7B 的 58.74% 和 Block Diff 4B 的 60.27%。这个表适合说明“接近 AR，而不是完全超过 AR”。
- 质量：Table 3 支撑 likelihood evaluation 的兼容性。TiDAR 8B 在 MMLU、ARC、Hellaswag、PIQA、Winogrande 等任务上的平均值为 75.40%，高于 Qwen3 8B 的 74.25%，也高于 Dream 7B 的 71.86% 和 LLaDA 8B 的 68.06%。这对 serving strategy 读者重要，因为它说明 TiDAR 不只在生成式任务上报速度，也能通过 pure causal mask 做类似 AR 的 likelihood 评估。
- 质量：Table 4 是防止“高 T/NFE 必然损质量”的关键证据。Confidence > 0.8 达到 Avg T/NFE 3.06 时，HumanEval Avg、MBPP Avg、GSM8k 分别为 28.96%、39.28%、47.54%；TiDAR 4 drafts 在 Avg T/NFE 3.47 时分别为 38.42%、50.96%、55.87%；TiDAR 8 drafts 在 Avg T/NFE 5.49 时分别为 39.94%、52.13%、54.74%。因此 Page 5 的判断应是：TiDAR 的质量-吞吐信号足够强，值得复现。
- 吞吐：Page 5 不能和 Page 6 混在一起讲 baseline 方法差异。此页只回答“论文证据是否足以让我们复现”：答案是 yes，但复现目标应是重测 quality-throughput frontier，而不是证明 production serving benefit。建议下游页面把 Figure 4 放在中心，旁边用 Table 2/3/4 的少量数字说明质量没有被 headline speedup 掩盖。
参考图片：
- ![Figure 4: Efficiency-Quality Benchmarking](brief-assets/picture_005-2.png)
- Figure 4 展示 TiDAR 在论文设置中相对 AR throughput speedup 与任务分数之间的关系。
- ![Table 2: Generative Evaluation Results](brief-assets/table_002.png)
- Table 2 展示 TiDAR 与 AR、Block Diffusion、Dream、LLaDA 等模型在 coding/math generative tasks 上的分数。
- ![Table 4: Comparing Different Decoding Strategies](brief-assets/table_004.png)
- Table 4 展示 TiDAR drafts 与 confidence decoding / left-to-right AR decoding 的 T/NFE 和质量差异。
备注：
- 这页必须保留“论文设置”措辞；不能把 relative AR throughput speedup 改成平台吞吐收益。

### Page 6: 对比要看三条轴
所属章节：再拆证据
页面标题：对比要看三条轴
标题说明：TiDAR 相比 AR、speculative decoding、diffusion baseline 的优势和公平性边界不同
分析总结：
- AR：质量参照最强，但一 token per step 限制 memory-bound 吞吐
- Speculative：EAGLE-3 是关键参照，但权重配对影响公平性
- Diffusion：并行潜力强，TiDAR 用 AR sampling 补质量边界
正文内容：
- AR：AR baseline 是质量参照，不是 TiDAR 要完全替代的背景板。论文动机指出 AR decoding 在 memory-bound 情况下每步只生成一个 token，不能充分利用现代 GPU 的 compute density；但 AR 的 causal factorization 与 language modeling 自然对齐，因此仍是质量上最重要的参照。Page 6 应让读者看到：TiDAR 的目标不是否定 AR，而是在保留 AR sampling 质量保护的同时利用 diffusion pre-drafting 提高单步产出。
- AR：Table 2/3 里 Qwen2.5、Qwen3、Llama、SmolLM 等 AR-family 模型给出了质量基线。TiDAR 8B generative average 低于 Qwen3 8B，但 likelihood average 高于 Qwen3 8B；这个混合结果意味着 deck 不应写“TiDAR 全面超过 AR”，而应写“在部分指标上接近或超过 AR，且显著提高论文设置下 relative throughput”。这个措辞更适合 serving platform leaders 的复现判断。
- Speculative：speculative decoding 是 serving 团队最熟悉的相邻路线。Table 1 把 Classic Speculative Decoding 标为 separate draft model、low drafting capacity、非 parallel-to-verification；EAGLE-3 / DeepSeek-V3 / Apple MTP 则是 shared with base 或 multi-token prediction line，但 drafting capacity 与并行关系不同。TiDAR 的差异是 shared high-capacity drafter、parallel decoding、parallel to verification 同时成立。
- Speculative：EAGLE-3 是关键参照，但 Page 6 必须保留公平性边界。论文 Figure 4 中使用 EAGLE-3 8B instruct 点做比较，同时脚注说明使用 Qwen3-8B instruct EAGLE-3 weights 是因为缺少对应 base model weights。下游页面可以把 EAGLE-3 标成 strong practical comparator，但不能写成“TiDAR 普遍击败所有 speculative decoding”。本地复现时需要重新选择可比模型、权重、任务和实现。
- Diffusion：Block Diffusion、Dream、LLaDA 是 parallelism 参照。论文指出 masked diffusion language models 有并行 token decoding 潜力，但在并行度和质量之间存在张力；质量最好时可能需要一 token per forward 或更保守 decoding，从而削弱系统收益。TiDAR 的优势主张是借 diffusion 做 pre-draft，用 AR sampling 保护最终输出质量，因此 Page 6 应把 diffusion baseline 的边界讲清楚，而不是泛泛说 diffusion 质量差。
- Diffusion：Figure 4 和 Table 2/3 都能支撑这个分法。Block Diffusion 在某些任务上有并行潜力，但 Table 2 中 1.5B Block Diff average 为 38.41%，TiDAR 1.5B 为 44.03%；8B 附近 Dream 7B average 为 58.74%，TiDAR Trust Diff 8B 为 65.31%。这些比较说明 TiDAR 的读法是“补 diffusion 的质量边界”，而非“只靠 diffusion 并行获胜”。
- Speculative：Page 6 的读者判断是 baseline comparison 是否公平、是否足以定位 TiDAR 的独特性。建议下游页面用 Table 1 重建为四列矩阵：AR 质量参照、speculative serving 近邻、diffusion parallelism 参照、TiDAR hybrid candidate。这样能把 Page 5 的结果证据和 Page 6 的方法比较拆清楚，避免变成泛泛实验总结。
参考图片：
- ![Table 1: Comparison among Speculative Frameworks](brief-assets/table_001.png)
- Table 1 展示 TiDAR 与 classic speculative decoding、APD、EAGLE-3、DeepSeek-V3、Apple MTP 的机制维度差异。
- ![Table 3: Likelihood Evaluation Results](brief-assets/table_003.png)
- Table 3 展示 TiDAR 与 AR / diffusion family 在 likelihood tasks 上的比较，适合补充质量参照。
备注：
- EAGLE-3 comparison 需要写清楚权重配对边界；不要写成 TiDAR 对 speculative decoding 的普遍胜利。

### Page 7: 上线前先过五道门
所属章节：最后验假设
页面标题：上线前先过五道门
标题说明：TiDAR 的 serving 价值取决于 batch、hardware、long context、kernel 与 scheduler 复测
分析总结：
- 口径门：batch=1/single H100 需扩到本地负载与硬件
- 实现门：long context、custom kernels、mask/KV 逻辑要算成本
- 集成门：scheduler 与 serving stack 决定 free slots 能否兑现
正文内容：
- 口径门：论文 efficiency benchmarking 聚焦 single H100、batch size = 1，并用 downstream generative task prompts 做 wall-clock throughput 对比。这个口径适合证明 TiDAR 的机制有速度信号，但不能覆盖本地 serving 的 batch 分布、prefill/decode 混合、continuous batching、multi-GPU、KV allocator、请求长度分布和 SLO。复现第一关应把 4.71x / 5.91x 拆成本地可测指标：tokens/s、TTFT、TPOT、P95/P99 latency、GPU utilization、accepted length 分布和失败样本。
- 口径门：hardware 不能只写 H100。Figure 1 的 free token slots 来自 Qwen3-32B on NVIDIA H100 with Flash Attention 2 的 profiling；不同 GPU、attention kernel、memory bandwidth、batching 形态和模型尺寸都可能改变 free / cheap token slot 区间。Page 7 应把 Figure 1 用作“需要复测的硬件假设”，而不是作为最终收益图。
- 实现门：long context 是论文自己留下的重点限制。论文限制部分说明当前实现训练时需要 appended mask tokens，等于需要更长序列；efficient long context extension，例如专门为 TiDAR 设计的 context parallelism，被留作 future work。对于 serving strategy deck，这意味着 TiDAR 不应先进入长上下文生产路线判断，而应先在短到中等上下文、明确 block length 的复现设置中验证。
- 实现门：custom kernels 是决定 free slots 能否兑现的技术门槛。论文写到 native PyTorch with Flex Attention 已有 throughput improvement，但 custom attention kernels 和 scheduling algorithms 可能进一步利用特定硬件上的 free token slots。下游页面应把这个说法写成工程依赖：如果本地没有合适 kernel、mask slicing 成本高、或者 proposal selection 带来额外同步，论文设置下的 relative speedup 可能无法转化为平台收益。
- 实现门：mask/KV 逻辑要单独算成本。TiDAR 需要处理 rejected tokens 对应 KV cache 的保存、丢弃或回滚；需要让不同样本的 accepted length 与下一步 proposals 对齐；还需要在 scheduler 中处理动态 draft length 或 block length。复现计划应记录这些状态管理成本，而不是只比较最终输出速度。
- 集成门：scheduler 与 serving stack integration 是最终判断门。TiDAR 的核心价值来自“同一次 forward 多带 token slots 仍然便宜”的假设；但生产 scheduler 可能已经通过 batching、prefix caching、KV paging、speculative head 或其他优化占用了同一片硬件余量。Page 7 应要求复现时对比现有 serving stack 的 baseline，而不是只对比论文中的 AR loop。
- 集成门：最终策略建议应是 staged gates。Gate 1 复现实验分数和 T/NFE；Gate 2 在本地硬件和 batch 分布下重测 throughput / latency；Gate 3 验证 long context 与 mask/KV 实现成本；Gate 4 评估 custom kernels 与 scheduler integration；Gate 5 才讨论是否进入平台策略。若任一 gate 失败，TiDAR 仍可作为研究跟踪对象，但不应进入部署路径。
参考图片：
- ![Figure 1: Latency Scaling over Token Slots](brief-assets/picture_002.png)
- Figure 1 展示 free / cheap token slots 的 profiling，是 Page 7 的 serving-assumption 主证据。
备注：
- 此页必须把 batch、hardware、long context、custom kernels、scheduler / serving stack integration 写成复现门槛。

