# PPT Content Brief

## Deck Metadata

主题：Aegaeon token-level GPU pooling architecture evaluation

目标读者：技术产品 / 基础设施领导，评估是否值得把 token-level GPU pooling 适配到多模型 LLM serving stack。

页数口径：7 页总页数；Page 1 cover，Page 2 summary，Page 3 contents，Page 4-7 为四页内容页。

核心结论：先评估，再承诺收益。Aegaeon 的生产 workload、SLO capacity 与 beta deployment 数字足以支持受控复测，但 Alibaba Cloud 的 82% GPU saving 不能直接写成我们 stack 的确定收益。

内容来源：Aegaeon paper package，已批准的 source-understanding review，以及少量相邻 serving 方向公开论文用于定位差异。

关联审计文件：research_audit.md

## Summary Page

页码：Page 2

页面标题：先评估，再承诺收益

标题说明：论文给出生产 workload 与 beta saving 强信号，但适配我们 stack 的成本收益必须用本地 serving gate 验证

分析总结：

- 为什么相关：长尾模型只贡献 1.35% 请求却占用 17.7% GPUs
- 为什么可试：Aegaeon 把 request-level scale decision 推到 token boundary
- 为什么谨慎：82% GPU saving 不能从 Alibaba Cloud 直接外推

正文内容：

- 为什么相关：这份 deck 的起点不是“论文提出了一个新系统”，而是“我们的多模型 serving 是否也存在类似资源浪费”。Aegaeon 的生产 workload 显示，779 个模型中 94.1% 属于低频长尾，只贡献 1.35% of 167.6M requests，却占用 17.7% of 30K GPUs。这个数字组合把问题从抽象的 GPU utilization 拉回到模型市场的资源驻留：长尾模型为了随时可服务而常驻资源，热门模型又会出现短时 request burst，导致 dedicated / reserved capacity 很难同时兼顾成本和 SLO。
- 为什么相关：对领导评估来说，Page 4 应先判断我们的 workload 是否像这个场景：模型数量是否足够多，流量 skew 是否明显，top models 是否有 burst，低频模型是否仍占用常驻 GPU，平均 request duration 是否让 active model count 长时间偏高。如果 workload 不匹配，后续 token-level pooling 的收益会被天然压缩；如果匹配，Aegaeon 的机制值得进入更具体的 serving component 复测。
- 为什么可试：Aegaeon 的技术抓手不是泛泛地“把更多模型放到一张 GPU”，而是把 scale decision 从 request granularity 推到 token boundary。request-level autoscaling 往往要等已有 request 完整结束才能释放 active model；token-level autoscaling 则尝试在 token 之间 preempt active model，让 pending model 更早进入服务。这个机制可以拆成可测组件：token-level scheduler、prefill scheduling、decoding scheduling、model switching path、KV cache movement/synchronization、engine lifecycle reuse。
- 为什么可试：prefill 和 decoding 的分离是这套机制能被复测的关键。prefill 面向 Time-To-First-Token，decoding 面向 Time-Between-Tokens；如果我们只看 end-to-end latency 或平均 throughput，就会误判它的 SLO 价值。Page 5 应要求本地复测同时看 TTFT、TBT、SLO violation、model switching latency 和 GPU utilization，而不是只跑一个 throughput benchmark。
- 为什么谨慎：Alibaba Cloud Model Studio beta deployment 是本 deck 最强的生产相关信号：论文报告服务 tens of models，参数规模从 1.8B 到 72B，GPU 需求从 1,192 降到 213，约 82% saving。这个数字可以支撑“值得排进 architecture evaluation 优先级”，但不能直接变成“我们也会省 82%”。我们的 serving stack 可能有不同模型组合、engine implementation、KV cache layout、memory manager、routing policy、fallback policy 和 SLO 定义，因此收益必须经本地 gate 证明。
- 为什么谨慎：最终建议的行动不是上线承诺，而是受控复测：先确认 workload similarity，再验证 token-boundary preemption 是否能在本地 SLO 定义下稳定运行，最后用小规模 before/after 数据看 SLO violation、GPU utilization、goodput/arrival-rate capacity 和 fallback 成本。只有这些 gate 通过后，才适合进入适配方案和收益 forecast。

参考图片：

- ![Figure 1: Concurrent LLM serving workloads](brief-assets/picture_002.png)
- Figure 1 展示模型调用 CDF 与热门模型 request burst，是“为什么相关”的主要源图。
- ![Figure 2: Request-level auto-scaling vs token-level auto-scaling](brief-assets/picture_003.png)
- Figure 2 展示 request-level 与 token-level scale decision 的差异，是“为什么可试”的主要源图。
- ![Figure 18: GPU utilization before and after deploying Aegaeon](brief-assets/picture_017.png)
- Figure 18 展示 beta deployment 前后 GPU utilization 曲线，是“为什么谨慎”的生产信号支撑。

备注：

- 可在页脚或讲者备注中保留一句谨慎表述：82% GPU saving 是 Alibaba Cloud Model Studio beta deployment 的报告值，本 deck 只把它作为复测优先级信号。

## Table of Contents

01 小标题：长尾浪费是真问题

说明：用生产 workload statistics 证明 Aegaeon 评估对象成立：低频模型占用 GPU，热门模型又有 burst 风险。

02 小标题：可试点在 token boundary

说明：把“为什么可试”讲具体：scale decision 从 request 推到 token，prefill/decoding 分离承载 TTFT/TBT。

03 小标题：证据够复测，迁移过 gate

说明：集中放 goodput / arrival-rate capacity、SLO 曲线与 beta saving，并把本地 serving gate 明确列出来。

## Page Content

### Page 4: 先判定 workload 像不像

所属章节：长尾浪费是真问题

页面标题：先判定 workload 像不像

标题说明：Aegaeon 的评估价值来自长尾模型常驻与热门模型 burst 并存；我们的流量若不匹配，后续机制收益会打折

分析总结：

- 匹配信号：779 个模型中 94.1% 长尾只贡献 1.35% 请求，却占用 17.7% GPUs
- 决策问题：先对齐模型数、请求 skew、burst pattern 和 request duration

正文内容：

- 匹配信号：Page 4 要帮助读者先判断“这个问题是不是我们的问题”。Aegaeon 的生产统计不是泛泛描述模型市场，而是给出了资源浪费的结构：在 779 个模型、167.6M requests、30K GPUs 的口径下，94.1% 的低频模型只贡献 1.35% 请求，却占用 17.7% GPU。这个组合说明 GPU 浪费来自低频模型的资源驻留，而不是单一模型的 kernel efficiency 或 batch size 不足。
- 匹配信号：Figure 1 的右侧 burst panel 说明热门模型也会产生预留压力。一个 top model 在 600 秒窗口内出现 request burst，burst 区域超过 reserved line；这意味着如果 serving stack 只按平均负载配额，热门模型会冲击 SLO，如果按峰值预留，长尾和热门模型都会增加 idle capacity。Page 4 应把长尾和突发并列呈现，避免把问题简化成“冷模型太多”。
- 匹配信号：Aegaeon 还指出 request execution time 较长会让大量模型保持 active。论文示例中，100 个模型、总 arrival rate 只有 3.7 req/s 时，平均 active model count 仍达到 46.55。这解释了为什么 request-level autoscaling 难以把 GPU pool 压到很少 active models：即便每个模型调用稀疏，长 request duration 仍会让模型处于不能被安全释放的状态。
- 决策问题：我们的第一组本地数据应包括模型数量、参数规模分布、请求量分布、top model burst amplitude、平均与 p95 request duration、active model count、当前 GPU reservation policy、低频模型占用 GPU 比例。如果这些指标显示长尾模型占用常驻资源且热门模型存在 burst，那么 Aegaeon 的问题设定与我们相近。
- 决策问题：如果我们的 model mix 更集中，例如少数模型贡献绝大多数请求且已经通过 batch serving 或 routing 聚合得很好，token-level GPU pooling 的收益可能低于论文场景；如果我们的低频模型也长期保留实例以避免 cold start 或 SLO violation，Aegaeon 的评估优先级就会升高。这个判断应在 Page 4 做完，再进入机制页。
- 决策问题：Page 4 的结论应是一个 gate，而不是论文摘要：只有 workload similarity 成立，后续 Page 5 的 token-boundary preemption、Page 6 的 capacity signal、Page 7 的 migration gates 才值得投入评估资源。

参考图片：

- ![Figure 1: Concurrent LLM serving workloads](brief-assets/picture_002-2.png)
- Figure 1 展示低频模型调用 CDF 与热门 270B model request burst。左侧数据用于说明长尾模型占用 GPU，右侧数据用于说明 reserved capacity 面对 burst 的压力。
- ![Figure 4: Active model count over time](brief-assets/picture_005.png)
- Figure 4 展示 active model count over time，支撑 request-level autoscaling 受 active model 数限制的判断。

备注：

- 本页不要讨论 Aegaeon 是否已经适配我们 stack，只判断 workload fit；如果 workload 不像，后续收益讨论要降级。

### Page 5: 机制可试，难点在切换

所属章节：可试点在 token boundary

页面标题：机制可试，难点在切换

标题说明：token boundary 让 scale decision 提前发生；prefill/decoding 分离承载 TTFT/TBT，但收益取决于切换成本是否被压住

分析总结：

- 调度抓手：request-level 等完整请求结束，token-level 可在 token 之间 preempt active model
- SLO 抓手：prefill 面向 TTFT，decoding 面向 TBT，分别调度才有复测价值
- 工程约束：engine reuse、explicit memory management 和 KV cache sync 决定是否跑得动

正文内容：

- 调度抓手：Aegaeon 的机制页要回答“为什么不是又一种普通 pooling”。request-level autoscaling 的限制是等待完整 request 结束：当 GPU 上所有 instances 都被 active models 占住时，新模型请求必须等某个 active request 完成，导致 head-of-line blocking。token-level autoscaling 把决策点推进到 token boundary，允许 active model 在生成 token 之间被 preemptively scale down，并让 pending model 更早 scale up。
- 调度抓手：Figure 2 可以作为核心对比图。上半部分 request-level 路径里，Model C arrival 后仍要等待 Model A/B 的 request-level completion；下半部分 token-level 路径里，不同模型在 token 序列之间交替进入 GPU。对领导读者来说，这张图的价值是说明“可试点”落在 serving scheduler 的 decision granularity，而不是抽象的系统架构愿景。
- 调度抓手：论文用 active-model 分析解释为什么 request-level pooling 难以突破 2-3 models/GPU：长 request service time 会把很多稀疏模型变成 active models。token-level preemption 的目标，是在不等完整 request 结束的情况下，缩短 pending model 的等待时间并提高 pool 的可服务模型数。
- SLO 抓手：prefill 与 decoding 分离是本页第二个机制点。prefill 处理 prompt 并生成 first token，主要关联 TTFT；decoding 每步只处理新 token，主要关联 TBT。Aegaeon 因此分别使用 grouped FCFS 和 weighted round-robin，目标是在不同阶段优化不同 SLO 风险。我们的复测也必须按 TTFT/TBT 拆开，否则可能把 first-token delay 与 token interval violation 混在一起。
- SLO 抓手：Page 5 应强调，token-level preemption 不是免费动作。每次 scale down / scale up 都可能带来 model loading、KV cache swap-out/swap-in、garbage collection、engine reinitialization 和 synchronization。只有在这些动作被压低并能与执行重叠时，token-boundary scheduling 才能变成 capacity improvement，而不是新的 latency source。
- 工程约束：论文声称通过 component reuse、explicit memory management、fine-grained KV cache synchronization 将 autoscaling overhead 降低 97%。对我们的 stack 来说，这三个 component 就是复测拆解项：engine reuse 能否避免完整 reinitialization，memory manager 能否缓存/预取 weights 并控制 fragmentation，KV cache sync 能否做到细粒度移动并让非关键操作被 overlap。
- 工程约束：本页最后应把机制转成可执行实验：测 model switching latency、KV cache movement latency、engine lifecycle breakdown、GPU/host memory cache hit rate、TTFT/TBT violation under preemption、goodput under model count changes。只要这些指标不可测或不可控，Page 6 的好数字就不能转成我们的适配信心。

参考图片：

- ![Figure 2: Request-level auto-scaling vs token-level auto-scaling](brief-assets/picture_003-2.png)
- Figure 2 展示 request-level 与 token-level autoscaling 的执行差异，适合放在机制页作为判断句的主要视觉支撑。
- ![Figure 7: Preemptive scaling process and initialization breakdown](brief-assets/picture_008.png)
- Figure 7 展示 preemptive scaling 默认流程、serving engine 组成与优化后 initialization breakdown，适合支撑“难点在切换”。
- ![Figure 10: Efficient scaling with fine-grained KV cache synchronization](brief-assets/picture_011.png)
- Figure 10 展示 fine-grained KV cache synchronization 的执行关系，可作为工程约束补充图。

备注：

- 本页避免把机制讲成论文实现细节堆叠；所有细节都要回到“我们能否复测并控制切换成本”。

### Page 6: 证据够复测，不够承诺

所属章节：证据够复测，迁移过 gate

页面标题：证据够复测，不够承诺

标题说明：SLO 曲线、arrival-rate/goodput 数字和 beta saving 支持排优先级；82% saving 仍只属于 Alibaba Cloud stack

分析总结：

- 容量信号：论文报告 2-2.5x arrival rate 或 1.5-9x goodput，并展示 SLO attainment 曲线
- 生产信号：beta deployment 服务 1.8B-72B 的 tens of models，GPU 从 1192 降到 213
- 边界信号：这些数字证明值得复测，不证明我们可直接拿到同等收益

正文内容：

- 容量信号：Page 6 要帮助读者判断“证据是否够排复测优先级”。Aegaeon 的摘要和结论报告，它相对 ServerlessLLM、MuxServe 等方案可支撑 2-2.5x higher request arrival rates，或 1.5-9x higher goodput。这个数字不应孤立出现，应与 Figure 11 或 Figure 13 的 SLO attainment 曲线一起讲：Aegaeon 的意义在于更高负载或更多模型数下仍维持较高 SLO attainment。
- 容量信号：Figure 11 以 ShareGPT workload 展示不同 RPS 和输入/输出设置下的 SLO attainment。Figure 13 展示随着 model count 或 average arrival rate 增加，不同系统的 SLO attainment 下降边界。对 architecture evaluation 而言，这类曲线比单点 throughput 更有用，因为它们直接对应“我们能多承载多少模型/请求而不明显扩大 violation”。
- 容量信号：Page 6 可以用一句话解释 controlled experiment 和 production signal 的关系：SLO 曲线证明机制在论文设定下有 capacity headroom，beta deployment 证明它在 Alibaba Cloud Model Studio 中进入过生产相关环境。两者结合足以支持复测，但仍不能跳过本地 serving gate。
- 生产信号：论文报告 Aegaeon beta deployed in Alibaba Cloud Model Studio for over three months，serving tens of models ranging from 1.8B to 72B parameters。GPU 需求从 1,192 降到 213，约 82% saving。Figure 18 展示 70-hour period 内部署前后的 GPU utilization，适合作为生产相关性的视觉支撑。
- 生产信号：这个生产数据应被表述为“strong signal for evaluation priority”。它证明 Aegaeon 不是纯模拟方案，也不是只在小型 benchmark 上有效；但它的适用环境包括 Alibaba Cloud 的 model marketplace、runtime、memory manager、routing、fallback policy 和 SLO definition，不能默认等价于我们的环境。
- 边界信号：本页必须主动防止误读。正确表达是：Aegaeon 报告的 82% GPU saving 说明它值得在我们 stack 里做 controlled retest；错误表达是：采用 Aegaeon 后我们将节省 82% GPU。正确表达是：SLO attainment 曲线说明 token-level pooling 有 capacity signal；错误表达是：所有多模型 serving 场景都必然优于 request-level autoscaling。
- 边界信号：Page 6 的结论可以收束为“批准复测，不批准承诺”。如果领导要一个决策动作，本页支持把 Aegaeon 放入 architecture evaluation backlog，并要求复测计划覆盖 Page 7 的 gates；它不支持直接立项生产迁移或成本削减 OKR。

参考图片：

- ![Figure 11: End-to-end SLO attainment under varying RPS with ShareGPT](brief-assets/picture_013.png)
- Figure 11 展示 ShareGPT workload 下不同 RPS 与输入/输出设置的 SLO attainment，支撑容量信号。
- ![Figure 13: SLO attainment under varying model count and arrival rate](brief-assets/picture_012.png)
- Figure 13 展示模型数和 arrival rate 增加时的 SLO attainment 边界，适合补充 Page 6 的 capacity 判断。
- ![Figure 18: GPU utilization before and after deploying Aegaeon](brief-assets/picture_017-2.png)
- Figure 18 展示 beta deployment 前后 70-hour GPU utilization 曲线，支撑生产信号。

备注：

- 本页可以在讲者备注中保留：所有 production saving 数字只代表 Alibaba Cloud Model Studio beta deployment，不代表我们的 forecast。

### Page 7: 过 gate，再谈适配

所属章节：证据够复测，迁移过 gate

页面标题：过 gate，再谈适配

标题说明：下一步不是复述 82% saving，而是用本地 workload、SLO、KV cache 和 engine lifecycle 验证 token-level pooling 是否可落地

分析总结：

- 准入 gate：先对齐 SLO 定义、model mix、request duration 和 burst pattern
- 工程 gate：实测 KV cache movement/sync、engine reuse 和 model switching latency
- 决策 gate：小规模复测同时看 SLO violation、GPU utilization 和 fallback 成本

正文内容：

- 准入 gate：Page 7 要把 deck 从“看起来有价值”推进到“下一步怎么拍板”。第一组 gate 是准入条件：我们的 model mix 是否足够长尾，top models 是否有 burst，request duration 是否让 active model count 持续偏高，当前 reserved GPU policy 是否带来 measurable idle capacity，模型参数规模是否覆盖需要 TP / multi-GPU 的大模型，以及是否存在不能被 preempt 的高优先级服务。
- 准入 gate：SLO 定义必须先统一。Aegaeon 使用 TTFT 与 TBT framing，SLO attainment 以 token generation times meeting deadlines 来定义。我们的产品可能使用 TTFT、TPOT/TBT、end-to-end latency、streaming smoothness、tail latency 或 violation penalty。复测前应明确哪些 SLO 是 hard constraints，哪些是 degradation budget，哪些模型或请求类型可被 preempt。
- 工程 gate：KV cache movement/sync 是迁移风险最高的 serving component。复测应测量 KV cache swap-out/swap-in volume、同步延迟、cache block movement list、GPU/CPU memory layout compatibility、与当前 attention/kernel/runtime 的兼容性，以及 fine-grained synchronization 是否能把非关键操作 overlap 掉。若 KV cache movement 不可控，token-level preemption 会把 capacity gain 变成 latency risk。
- 工程 gate：engine lifecycle/reuse 决定 model switching latency。Aegaeon 的优化依赖 component reuse、explicit memory management 和 model/cache 预取；我们的 runtime 要逐项 profile tokenizer、communication group、distributed executor、model loading、profiling / optimization、scheduler state、log / metrics components。复测应给出 before/after switching latency breakdown，而不是只报告最终 goodput。
- 工程 gate：model switching latency 必须和 token-level scheduling 放在同一个实验里看。一个切换动作如果比 token interval 或 TBT budget 大很多，调度策略再好也会制造 violation；如果切换动作足够小并能与 execution overlap，token-level pooling 才可能提高 effective model count。
- 决策 gate：小规模复测建议分三步：第一步离线 replay workload，验证 model mix、request skew 和 burst pattern；第二步在 staging serving stack 中测 token-level preemption 的 TTFT/TBT/SLO violation、KV cache movement、engine lifecycle 和 switching latency；第三步做小规模 live shadow 或 canary，观察 GPU utilization、goodput/arrival-rate capacity、fallback 成本和异常恢复。
- 决策 gate：领导可拍板的下一步不是“适配 Aegaeon”，而是“批准一个 bounded evaluation”。进入下一轮的成功条件应包括：SLO violation 不扩大到不可接受范围，GPU utilization 或 goodput 有可解释提升，fallback path 不破坏服务稳定性，切换成本可被稳定控制，且结果能区分 workload fit 与 mechanism fit。
- 决策 gate：如果复测失败，也应产出可用结论：workload 不像、SLO 口径不兼容、KV cache movement 太贵、engine reuse 不成立、或 model switching latency 超过 TBT budget。这样的失败结论仍能帮助团队避免把 Alibaba Cloud 的 82% saving 错当成本地收益承诺。

参考图片：

- ![Figure 7: Preemptive scaling process and initialization breakdown](brief-assets/picture_008-2.png)
- Figure 7 展示 engine initialization 与优化后的 time breakdown，可作为 engine lifecycle/reuse gate 的例子。
- ![Figure 9: Explicitly managed memory in Aegaeon](brief-assets/picture_010.png)
- Figure 9 展示 GPU/host memory management 和 unified KV cache 操作，适合支撑 KV cache movement/sync gate。
- ![Figure 10: Fine-grained KV cache synchronization](brief-assets/picture_011-2.png)
- Figure 10 展示 fine-grained KV cache synchronization，可作为工程 gate 的技术检查项。

备注：

- Page 7 的结尾建议用明确动作：批准受控复测；不批准直接迁移；不把 82% saving 写入成本承诺。
