# PPT Content Brief

## Deck Metadata
主题：R-CLA / stochastic KV routing 是否值得进入 LLM serving 受控复测
目标读者：LLM serving / 推理基础设施工程负责人和技术产品决策者
页数口径：7 页总页数；Page 1 封面，Page 2 顶层总结，Page 3 目录，Page 4-7 正文内容页
核心结论：depth-wise KV sharing 不是替代现有 KV 压缩路线，而是补上 layer 轴容量实验；当前建议是先做受控复测，再讨论上线可能性
内容来源：Stochastic KV Routing paper package；H2O、KIVI、GQA、Cross-layer Attention Sharing、PyramidKV 等对比资料
关联审计文件：research_audit.md

## Summary Page
页码：Page 2
页面标题：先复测，再谈上线
标题说明：depth-wise KV sharing 不是替代现有压缩，而是补上 layer 轴容量实验
分析总结：
- 正交路线：token、bit、head 之外再压 layer
- 工程信号：g=4 让 8K batch 16 从 OOM 变可跑
- 验证门槛：质量迁移、训练成本、TTFT/throughput
正文内容：
- 正交路线：这页要先帮读者换坐标系。token eviction / SnapKV / PyramidKV 这类路线主要回答“哪些 token state 可以少存或晚存”，KV quantization / KIVI 回答“每份 KV state 可以用多低 bit 表示”，GQA/MQA 回答“同一层里多少 query heads 共享 KV heads”。R-CLA 讨论的是另一件事：不同 layer 是否必须各自保留一份 KV，还是可以在相邻层之间共享或复用前层 KV。这让它更像一个新增容量旋钮，而不是替代已有压缩栈的单点方案。
- 正交路线：因此顶层判断不能写成“R-CLA 比 token eviction 更好”或“R-CLA 取代 quantization”。更准确的表达是：R-CLA 对 serving 团队有复测价值，因为它补上 layer/depth 轴；如果它在本地模型族成立，后续才有资格讨论与 token eviction、KV quantization、paged KV、continuous batching 的组合方式。
- 工程信号：论文最能打动 serving 读者的是容量数据。Table 4 在 Qwen3-8B-like、36 layers、8 KV heads、bfloat16、单 80GB GPU、batch size 1 条件下显示，8K 输入时 g=4 将 KV cache 从 1170MB 降到 293MB；2K、16K、32K 行也都接近四分之一。Table 5 在 8,192-token context 下进一步给出 batch scaling：batch size 16 时 g=1 超出显存，g=4 仍能以 60,306MB peak memory 完成。
- 工程信号：质量侧不能只看容量。Table 2 在 Llama-3.1-8B、Mistral-7B、Qwen3-8B 与 HotpotQA、MSMarco、RepLiQA、SQuAD v2、TriviaQA 上显示，低 retention 时 R-CLA 通常显著优于 Base；Table 3 说明它比固定 CLA@k 更能跨 retention 档位保持表现。这个信号足够支撑“复测”，但仍应被表述为 QA retention 下的保真线索。
- 验证门槛：上线前必须同时过三道门槛。第一，质量迁移：内部长上下文、多轮、RAG、工具调用或目标线上任务不能只继承 QA 数据集结论。第二，训练成本：R-CLA 需要训练或微调接入，必须计算 token budget、GPU 成本、收敛速度、版本管理和回滚成本。第三，服务指标：TTFT、decode throughput、peak memory、可跑 batch、cache allocator、scheduler 和 kernel 支持必须在本地 backend 复测。
参考图片：
- ![Figure 4: R-CLA 训练期随机读取前层 KV、推理期确定共享](brief-assets/picture_005.png)
- Figure 4 展示 R-CLA 的训练/推理分工，可作为顶层页右侧机制小图：训练期制造层间扰动，推理期按固定 group 共享 cache。
- ![Table 5: 8K context 下 batch size scaling](brief-assets/table_005.png)
- Table 5 说明 8K batch 16 的“不可运行 / 可运行”差异，是顶层页最适合突出的一条工程信号。
备注：
- 建议页面口吻保持“受控复测建议”，不要写成“已满足上线条件”。

## Table of Contents
01 小标题：先看优化轴
说明：说明 R-CLA 为什么不是 token eviction / KV quantization 的替代品，而是补上 layer/depth 维度的容量实验。

02 小标题：再看可行性
说明：解释随机训练、确定共享的 R-CLA 机制，并用容量与质量结果判断是否值得复测。

03 小标题：最后看门槛
说明：把训练/微调成本、质量迁移、TTFT/throughput 和本地 backend 指标变成上线前验证清单。

## Page Content

### Page 4: 不是替代，是补轴
所属章节：先看优化轴
页面标题：不是替代，是补轴
标题说明：R-CLA 绕开 token、bit、head 三条熟路，直接验证 layer/depth 冗余
分析总结：
- 路线差异：现有压缩改 token 或 bit，R-CLA 改层间 KV 来源
- 组合价值：正交才值得复测，不能预设收益相乘
正文内容：
- 路线差异：这页要把“KV cache 优化”拆成几条并列轴，而不是把所有方法混成一类。H2O、SnapKV、PyramidKV 等 token/time 轴方法判断哪些 token 或 chunk 值得保留；KIVI、KVQuant 等 bit 轴方法减少每个 KV state 的表示成本；GQA/MQA 沿 head 轴减少同层 KV heads；R-CLA 才是沿 layer/depth 轴改变 KV 来源，让多个层在推理时共享或复用前层 KV。
- 路线差异：这一区分对工程评审很关键。token eviction 的主要风险是信息丢失、动态选择成本和预填充峰值未必下降；KV quantization 的主要风险是低 bit 精度、kernel 支持和误差累积；R-CLA 的主要风险则是模型必须通过训练或微调适配层间共享。三类问题不是同一个旋钮，所以不能用“谁替代谁”的方式讨论。
- 路线差异：GQA/MQA 是容易混淆的对照。GQA 让同一层内多个 query heads 共享较少 KV heads，Qwen3-8B-like 的实验口径已经是 8 KV heads；R-CLA 的问题是即使同层 head 已经共享，不同 layer 是否还必须各自存 KV。换句话说，R-CLA 是在现代结构已用 GQA 的情况下继续压 depth 轴。
- 组合价值：正交性提供复测价值，但不保证组合收益。R-CLA 原则上可以和 token eviction、KV quantization、paged KV、continuous batching 同时存在；但组合后可能出现质量损失放大、cache allocator 更复杂、kernel 路径不匹配或调度收益被抵消。因此页面结论应是“值得独立复测并设计组合实验”，不是“收益可以相乘”。
- 组合价值：这一页的读法可以是左侧方法地图、右侧判断句。读者先看到四条轴，再看到 R-CLA 所处位置，最后看到复测含义：如果我们只验证 token eviction 或 quantization，就仍然不知道 layer/depth 冗余是否能转化为本地 serving 容量收益。
参考图片：
- 无必用源图。建议下游用简化方法地图表达 `token/time`、`bit`、`head`、`layer/depth` 四条轴，并把 R-CLA 标在 `layer/depth` 轴；该图是叙事辅助，不应伪装成论文原图。
备注：
- 避免把 H2O、KIVI、GQA 写成 R-CLA 的失败对手；它们是不同轴的对照和潜在组合项。

### Page 5: 随机训练，确定共享
所属章节：再看可行性
页面标题：随机训练，确定共享
标题说明：R-CLA 训练期随机读前层 KV，推理期按固定 group 共享 cache
分析总结：
- 机制核心：把未知硬件约束变成训练时见过的层间扰动
- 工程代价：收益来自模型适配，不是纯 runtime 开关
正文内容：
- 机制核心：R-CLA 的关键动作发生在训练或微调阶段。对于某一层 l，模型以概率 p 使用自己的 K/V states，以概率 1-p 读取随机选择的前层 l' 的 K/V states。这个过程让模型在训练中反复遇到不同 depth-wise sharing pattern，学会在缺少本层专属 KV 时仍然抽取可用信息。
- 机制核心：推理阶段不做随机选择，而是使用固定 deterministic sharing scheme。例如 g=4 时，每 4 个连续层形成一组，中间层复用组内保留层的 KV cache；这意味着推理路径可以围绕固定 group 来实现，而不是每个请求都运行随机路由。
- 机制核心：Figure 4 非常适合解释这一点：左侧是训练期 stochastic KV routing，层可能 self-attend，也可能 cross-attend 到前层 KV；右侧是推理期 deterministic sharing，同一组层共享固定 KV。页面正文应强调“随机只用于适配模型，推理目标是确定可执行的共享策略”。
- 工程代价：这也说明 R-CLA 不是纯 runtime 开关。token eviction 或某些 KV quantization 方法可以在不改模型权重的情况下先做 serving 侧实验；R-CLA 的收益来自模型见过层间 KV 缺失或替换，因此必须把微调数据、训练资源、模型版本、回滚策略和上线灰度纳入成本。
- 工程代价：论文的附录还提示 fine-tuning 训练动态会变慢或表现出正则化式影响；这对 infra 决策者不是坏事也不是好事，而是复测必填项。建议后续实验记录 train loss、eval loss、收敛步数、过拟合拐点、目标任务质量和不同 p 值下的容量收益。
- 工程代价：页面收束时可以提醒读者：R-CLA 的工程价值来自“用训练阶段的不确定性换推理阶段的确定共享”，而不是“推理时随便丢层 KV”。这个 distinction 可以避免把方法误读成粗暴 cache dropping。
参考图片：
- ![Figure 4: R-CLA 训练期随机路由与推理期确定共享](brief-assets/picture_005-2.png)
- Figure 4 展示训练期每层可能读取自己的 KV 或前层 KV，推理期同一 group 内共享固定 KV cache；这张图应作为机制页的主图。
备注：
- 不要把 group size 写成唯一推荐值；g=4 是论文表格中的关键实验点，复测时仍应比较 g=2、g=4 和目标显存压力点。

### Page 6: 信号够复测
所属章节：再看可行性
页面标题：信号够复测
标题说明：g=4 给出约 4x KV 降幅和 batch 可运行性，QA retention 证明质量不必同步崩塌
分析总结：
- 容量结果：8K KV cache 从 1170MB 降到 293MB
- 质量结果：R-CLA 在低 retention QA 中显著优于 Base
- 适用范围：单卡和 QA proxy 不能等同生产 SLO
正文内容：
- 容量结果：Table 4 是容量判断的第一张主表。在 Qwen3-8B-like、36 layers、8 KV heads、bfloat16、单 80GB GPU、batch size 1 条件下，g=4 在所有列示输入长度上都把 KV cache 降到约四分之一。8K 输入行最适合做页面主数字：g=1 是 1170MB，g=4 是 293MB；TTFT 从 297ms 到 286ms，throughput 从 34.0 tok/s 到 41.6 tok/s。
- 容量结果：Table 5 把容量收益转成更接近 serving 的 batch scaling 信号。在 8,192-token context 下，batch size 2、4、8 时 g=4 都降低 peak memory 和 KV cache；batch size 16 时 baseline g=1 超出显存，而 g=4 仍以 60,306MB peak memory、4,643MB KV cache、4696ms TTFT、8.0 tok/s 完成。这条数据可以作为“为什么值得复测”的工程钩子。
- 质量结果：Table 2 说明 R-CLA 不只是省 cache 后让质量崩塌。它在 Llama-3.1-8B、Mistral-7B、Qwen3-8B 上比较 Base 和 R-CLA，并覆盖 HotpotQA、MSMarco、RepLiQA、SQuAD v2、TriviaQA 三档 retention。低 retention 下，R-CLA 通常显著优于 Base；例如 Qwen3-8B 在 HotpotQA 25% retention 下 F1 从 0.011 到 0.098，TriviaQA 25% retention 从 0.005 到 0.131。
- 质量结果：Table 3 进一步解释为什么要看随机训练而不只看固定 CLA@k。固定 CLA@2 或 CLA@4 可能在某个 retention 点表现接近，但跨 100%、50%、25% retention 时更容易退化；R-CLA 的价值在于用一个训练过程覆盖多个潜在部署约束，这和“未知硬件约束”场景更匹配。
- 适用范围：这页必须把“复测”和“上线”分开。Table 4/5 是单卡实验，不覆盖本地 serving backend 的 paged KV、continuous batching、多租户调度、CUDA graph、MoE、speculative decoding 或真实 SLO；Table 2/3 是 QA retention proxy，不等于内部业务任务质量。最稳妥的结论是：容量和质量信号足够立项复测，但还不足以承诺生产收益。
- 适用范围：页面可以用“强信号 / 待复测”两层表达。强信号是 4x 左右的 KV cache 降幅、batch 16 从 OOM 到可运行、低 retention QA 质量改善；待复测是训练成本、本地任务质量、端到端 TTFT/throughput、cache allocator、调度和与现有压缩栈组合后的结果。
参考图片：
- ![Table 4: 不同输入长度下的推理效率](brief-assets/table_004.png)
- Table 4 说明 g=4 在 2K、8K、16K、32K 输入长度下都把 KV cache 降到约四分之一，并列出 TTFT 与 throughput。
- ![Table 5: 8K context 下 batch size scaling](brief-assets/table_005-2.png)
- Table 5 说明 batch size 16 时 baseline 超显存，而 g=4 可完成，是最接近工程容量门槛的表格。
- ![Table 2: R-CLA 在 QA retention 下的 F1 结果](brief-assets/table_002.png)
- Table 2 展示不同模型、数据集和 retention 下 Base 与 R-CLA 的 F1 对比，可用来支持“质量不必同步崩塌”的判断。
- ![Table 3: R-CLA 与 CLA@k / RD-CLA@k 的对比](brief-assets/table_003.png)
- Table 3 展示 R-CLA 相对固定 CLA@k 的跨 retention 稳定性，可作为本页补充图或备选附图。
备注：
- 如果页面空间有限，优先保留 Table 4/5 的容量证据；质量表可以转成 2-3 个数字 callout。

### Page 7: 过三关再上线
所属章节：最后看门槛
页面标题：过三关再上线
标题说明：本地复测必须同时证明质量迁移、训练成本可控、serving 指标成立
分析总结：
- 质量门槛：内部任务不能只继承 QA retention 结论
- 成本门槛：训练或微调接入要算资源和版本管理
- 服务门槛：TTFT、throughput、peak memory 要在本地 backend 复测
正文内容：
- 质量门槛：第一关是质量迁移。论文的质量信号来自 QA retention 任务，适合证明“共享 KV 后质量未必同步崩塌”，但不等于我们的线上任务质量。复测任务应覆盖内部长上下文问答、多轮对话、RAG 输入、工具调用、代码或目标业务流，并且同时看 full retention、50% retention、25% retention 或本地计划使用的 group size。
- 质量门槛：质量评估不能只看平均分。需要观察低频失败、长上下文中间信息丢失、引用错位、拒答/幻觉变化、工具参数准确率和多轮状态保持。R-CLA 的层间共享可能改变模型对上下文细节的保存方式，复测要包含人工抽样或红队样例，而不只是 benchmark 数字。
- 成本门槛：第二关是训练或微调成本。R-CLA 的收益来自模型适配，所以复测计划要写清楚训练数据、token budget、GPU 小时、p 值、group size、学习率、收敛曲线、eval loss、是否延缓过拟合、是否需要重新导出权重和服务镜像。若接入成本接近重新训练一条模型线，容量收益就必须足够大才值得继续。
- 成本门槛：版本管理也要进入评估。R-CLA 可能产生一个与 Base 不同的权重分支，后续要回答安全评测、回滚、灰度、监控、线上 A/B、兼容 tokenizer / adapter / LoRA / MoE 路线等问题。把这些成本放进页面，是为了避免“表格省显存”被误解为“上线成本很低”。
- 服务门槛：第三关是本地 serving 指标。复测必须在本地 backend 上同时记录 TTFT、decode throughput、peak memory、可跑 batch、P50/P95/P99 latency、SLO violation、GPU utilization、cache allocator 行为、continuous batching、paged KV、CUDA graph、kernel 路径和调度稳定性。Table 4/5 是很好的起点，但不能替代本地服务栈。
- 服务门槛：组合实验要谨慎设计。R-CLA 与 token eviction、KV quantization、paged KV 可能有正交收益，也可能出现误差叠加或实现复杂度抵消收益。建议复测顺序是先做 Base vs R-CLA 的单变量实验，再逐步加入现有压缩栈；每一步都保留质量、容量和延迟三类指标。
- 页面结尾建议：只有当质量迁移、成本可控和服务指标三关同时通过，才进入小流量生产试验讨论；如果任一关失败，应停留在研究或工程实验状态。这样既保留 R-CLA 的路线价值，也保护上线决策不被单篇论文的局部数据推着走。
参考图片：
- 无必用源图。建议下游用复测门槛表表达三关：质量迁移、训练成本、服务指标；表格来自本文已批准判断，不作为论文原图。
备注：
- 这一页是 deck 的风险刹车。不要把标题改成“上线计划”或“落地路径”，否则会弱化前面批准的判断边界。
