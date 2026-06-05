# Research Audit

## Research Frame

Task: prepare a PPT-ready content brief for an internal serving architecture evaluation deck about Aegaeon token-level GPU pooling.

Workspace root: `docs/showcase/published-run`

Target reader: technical product / infrastructure leadership evaluating whether token-level GPU pooling is worth adapting to their multi-model LLM serving stack.

Reader's likely starting belief: GPU pooling is attractive for OPEX, but serving stack migration carries scheduler, SLO, memory, KV cache, and runtime lifecycle risk.

Desired belief change: Aegaeon is worth bounded architecture evaluation and local retesting, but Alibaba Cloud's beta deployment saving must not be treated as guaranteed benefit for our stack.

Final use: pre-PPT content brief for an internal serving architecture evaluation deck.

Approved page count: 7 total PPT pages, including cover, summary page, and contents page.

Primary source package:

- `forward-tests/ppt-deep-search\aegaeon-gpu-pooling-hitl\candidate\input\pdf_xml\final\Aegaeon Effective GPU Pooling for Concurrent LLMServing on the Market.xml`
- `forward-tests/ppt-deep-search\aegaeon-gpu-pooling-hitl\candidate\input\pdf_xml\final\images\`

## Source Understanding

Approved source-understanding review:

- `docs/showcase/published-run`
- `docs/showcase/published-run`

Key understanding approved by the user:

- Aegaeon targets production-like multi-model LLM serving on a model marketplace, where long-tail low-frequency models and bursty hot models create GPU waste.
- The mechanism is token-level auto-scaling, with prefill/decoding disaggregation, TTFT/TBT-aware scheduling, component reuse, explicit memory management, and fine-grained KV cache synchronization.
- Strong source numbers include 94.1% of 779 models accounting for 1.35% of 167.6M requests while using 17.7% of 30K GPUs; 2-2.5x higher request arrival rates or 1.5-9x more goodput; beta deployment serving tens of models from 1.8B to 72B and reducing GPUs from 1,192 to 213.
- Non-negotiable boundary: Alibaba Cloud beta deployment and 82% GPU saving are strong signals, not guaranteed savings for our serving stack.

Important source figures/tables inspected:

- Figure 1 / `picture_002.png`: concurrent LLM serving workloads, long-tail CDF and hot-model burst.
- Figure 2 / `picture_003.png`: request-level auto-scaling vs token-level auto-scaling.
- Figure 4 / `picture_005.png`: active model count over time, estimated E[m] = 46.55.
- Figure 7 / `picture_008.png`: preemptive scaling process and inference engine initialization breakdown.
- Figure 9 / `picture_010.png`: explicitly managed memory in Aegaeon and unified KV cache operation.
- Figure 10 / `picture_011.png`: fine-grained KV cache synchronization.
- Figure 11 / `picture_013.png`: end-to-end SLO attainment under varying RPS with ShareGPT.
- Figure 13 / `picture_012.png`: SLO attainment under varying model count and arrival rate.
- Figure 18 / `picture_017.png`: GPU utilization before and after Aegaeon deployment.

## Executive Thesis

Approved thesis: "先评估，再承诺收益."

The deck should argue that Aegaeon is relevant enough for bounded architecture evaluation because it connects production workload statistics, token-level scale decision, SLO-aware scheduling, and beta deployment evidence. It should also make clear that the Alibaba Cloud beta deployment result is not directly transferable to our stack without local workload, SLO, KV cache, engine lifecycle, model mix, and switching-cost validation.

## Reader Cognitive Path

1. Start from the reader's decision: whether to invest in adapting token-level GPU pooling.
2. Establish workload fit before mechanism: if our model market is not long-tail and bursty, Aegaeon's upside weakens.
3. Explain mechanism as testable components: token boundary scale decision, prefill/decoding split, TTFT/TBT scheduling, switching-cost optimizations.
4. Weigh evidence: SLO curves and beta deployment justify retesting priority, not production commitment.
5. End with local gates: SLO definition, KV cache movement/sync, engine lifecycle/reuse, model mix, switching latency, SLO violation, GPU utilization, fallback cost.

## Pyramid Outline

Top-level summary page:

- Page 2: 先评估，再承诺收益

Supporting chapter claims:

- 长尾浪费是真问题: workload fit determines whether evaluation is relevant.
- 可试点在 token boundary: mechanism is concrete and decomposable, but switching cost is the hard part.
- 证据足够支持复测: source evidence is enough to prioritize retesting, but not enough to promise savings.
- 迁移要过本地 gate: adaptation should proceed only after local serving gates pass.

## Chapter Logic

Chapter 01: 长尾浪费是真问题

- Uses production workload statistics and burst behavior to decide whether the Aegaeon problem applies to our environment.
- Does not discuss implementation yet.

Chapter 02: 可试点在 token boundary

- Explains the mechanism at the level needed for architecture evaluation.
- Makes token boundary, prefill/decoding split, TTFT/TBT, and switching-cost components explicit.

Chapter 03: 证据足够支持复测

- Uses controlled SLO/capacity curves and beta deployment numbers to justify retesting priority.
- Separates Alibaba Cloud results from our expected benefit.

Chapter 04: 迁移要过本地 gate

- Converts the previous pages into local evaluation gates and next-step decision criteria.
- Keeps the recommendation bounded: approve retest, not direct migration.

## Page Logic Audit

Page 2

- Role: top-level answer for leadership.
- Approved visible viewpoint: `先评估，再承诺收益`; the local serving gate must validate cost/benefit before any commitment.
- Supported decision: approve architecture evaluation and local retest, not guaranteed adoption.

Page 4

- Role: help the reader judge workload match.
- Approved visible viewpoint: `先判定 workload 像不像`.
- Supported chapter claim: Aegaeon matters only if our multi-model serving has long-tail residency and bursty hot models.
- Boundary: do not move to benefits before workload similarity is tested.

Page 5

- Role: help the reader judge whether the mechanism is testable.
- Approved visible viewpoint: `机制可试，难点在切换`.
- Supported chapter claim: token boundary, prefill/decoding split, and TTFT/TBT scheduling are concrete; switching cost is the gating risk.
- Boundary: do not present token-level pooling as a scheduler-only change.

Page 6

- Role: help the reader judge whether evidence is enough for retest.
- Approved visible viewpoint: `证据够复测，不够承诺`.
- Supported chapter claim: SLO curves, arrival-rate/goodput claims, and beta deployment numbers justify priority.
- Boundary: 82% GPU saving belongs to Alibaba Cloud Model Studio and must not become our forecast.

Page 7

- Role: help the reader judge migration gates and next steps.
- Approved visible viewpoint: `过 gate，再谈适配`.
- Supported chapter claim: local workload, SLO, KV cache, engine lifecycle, model mix, switching cost, SLO violation, GPU utilization, and fallback cost must be measured before adaptation.
- Boundary: next action is bounded evaluation, not production rollout.

## Claim Evidence Implication Table

| Claim | Evidence | Implication |
| --- | --- | --- |
| The workload problem is production-relevant when long-tail models occupy GPU despite low request share. | Aegaeon Figure 1 and introduction: 94.1% of 779 models, 1.35% of 167.6M requests, 17.7% of 30K GPUs. | Page 4 should start with workload similarity, not mechanism enthusiasm. |
| Request-level auto-scaling is bounded by active model count. | Aegaeon introduction and Figure 4: at total arrival rate 3.7 req/s, estimated active models = 46.55 out of 100. | Token-level preemption is worth considering only if our request duration also keeps models active for long windows. |
| Aegaeon offers a concrete testable mechanism. | Figure 2 shows request-level vs token-level auto-scaling; text describes prefill grouped FCFS and decoding weighted round-robin; Figure 7/9/10 show switching and KV cache optimizations. | Page 5 should decompose the mechanism into scheduler, SLO, and engineering gates. |
| Aegaeon has capacity evidence under SLO framing. | Abstract/conclusion report 2-2.5x higher request arrival rates or 1.5-9x more goodput; Figure 11/13 show SLO attainment curves. | Page 6 can justify retest priority with capacity/SLO evidence. |
| Aegaeon has production-related deployment evidence. | Abstract/evaluation/conclusion: beta deployed over three months in Alibaba Cloud Model Studio, serving tens of models from 1.8B to 72B, GPU count 1,192 to 213; Figure 18 shows utilization. | Page 6 can show strong production signal. |
| Alibaba Cloud's 82% saving is not our guaranteed saving. | Deployment result is tied to Alibaba Cloud stack and workload; no source evidence validates our stack. | Page 6 and Page 7 must preserve non-extrapolation language. |
| Local adaptation depends on concrete serving gates. | Mechanism depends on TTFT/TBT definitions, KV cache movement/sync, engine lifecycle/reuse, model mix, and switching latency. | Page 7 should end with a retest plan and pass/fail gates. |

## Evidence Map

| Evidence item | Source locator | Type | Strength | Boundary / uncertainty | PPT relevance |
| --- | --- | --- | --- | --- | --- |
| 94.1% of 779 models contribute 1.35% of 167.6M requests but use 17.7% of 30K GPUs. | Primary XML introduction; Figure 1; `picture_002.png`. | source | strong | Alibaba Cloud Model Studio workload; our distribution unknown. | Must use as source figure or rebuilt statistic. |
| Hot 270B top model has burst above reserved line. | Figure 1(b); `picture_002.png`. | source | strong | Specific model / cluster sample; burst pattern may differ locally. | Use to show long-tail plus burst, not just cold models. |
| 46.55 active models out of 100 at total arrival rate 3.7 req/s. | Primary XML introduction; Figure 4; appendix active model analysis; `picture_005.png`. | source/calculation from paper | medium-strong | Depends on Poisson/request-duration assumptions. | Use as body support, not necessarily a headline. |
| Token-level auto-scaling can preempt active model between tokens. | Figure 2; primary XML Aegaeon overview. | source | strong | Diagrammatic mechanism; implementation cost must be tested. | Must use or summarize on Page 5. |
| Prefill and decoding scheduled separately around TTFT and TBT. | Primary XML Aegaeon overview / token-level scheduling. | source | strong | Local SLO definitions may differ. | Use on Page 5 and Page 7. |
| Autoscaling overhead reduced by 97%. | Primary XML abstract/contribution text; Figure 7/9/10 support optimization path. | source | medium | Summary number needs local decomposition; not enough alone for migration. | Use as engineering signal with caveat. |
| 2-2.5x higher request arrival rates or 1.5-9x goodput. | Primary XML abstract/evaluation/conclusion. | source | strong for paper claim | Controlled setup; local stack unknown. | Use on Page 6. |
| SLO attainment curves under ShareGPT and model-count/RPS variation. | Figure 11 / Figure 13; `picture_013.png`, `picture_012.png`. | source | strong | Benchmark/workload-specific. | Use at least one on Page 6. |
| Beta deployment over three months, tens of models, 1.8B-72B parameters, 1,192 to 213 GPUs. | Primary XML evaluation and abstract/conclusion. | source | strong for Alibaba Cloud | Does not prove our benefit. | Use on Page 6 with explicit non-extrapolation. |
| Figure 18 deployment utilization over 70 hours. | Figure 18; `picture_017.png`. | source | medium-strong | Utilization graph does not alone prove SLO preservation. | Use as production signal. |
| vLLM/PagedAttention is memory-management oriented and reports 2-4x throughput. | arXiv:2309.06180. | supplemental | medium | Adjacent context only. | Use only in source review/audit, not necessary in final PPT body. |
| MuxServe reports up to 1.8x throughput or 2.9x more requests within 99% SLO. | PMLR ICML 2024 page. | supplemental | medium | Adjacent baseline/context; not the deck's proof. | Use only as background if needed. |
| DistServe separates prefill/decoding and reports 7.4x more requests or 12.6x tighter SLO. | arXiv:2401.09670. | supplemental | medium | Adjacent phase-disaggregation context. | Use only as background if needed. |
| HydraServe reduces cold-start latency and improves SLO attainment. | arXiv:2502.15524. | supplemental | medium | Serverless cold-start context; not direct token-level pooling proof. | Use only as comparison context. |

## Source Usage Policy

Figures/tables:

- Figure 1 / `picture_002.png`: must use or summarize/rebuild. It is the strongest source figure for workload fit.
- Figure 2 / `picture_003.png`: must use or summarize. It explains the request-level versus token-level decision shift.
- Figure 4 / `picture_005.png`: may use as supporting evidence for active-model bottleneck.
- Figure 7 / `picture_008.png`: may use for switching-cost and engine lifecycle discussion.
- Figure 9 / `picture_010.png`: may use for explicit memory management and unified KV cache.
- Figure 10 / `picture_011.png`: may use for fine-grained KV cache synchronization.
- Figure 11 / `picture_013.png`: should use for SLO/capacity evidence if space permits.
- Figure 13 / `picture_012.png`: should use for SLO attainment under model-count / arrival-rate variation if space permits.
- Figure 18 / `picture_017.png`: should use or summarize for deployment signal.
- Figure 5 system overview: background only. Avoid making it a central visual because the user requested less generic system diagram usage.

Numeric claims:

- Production workload numbers can be used as source-backed facts for Alibaba Cloud Model Studio.
- 82% GPU saving can be used only as Alibaba Cloud beta deployment result.
- Any local expected saving must be omitted or marked as a future forecast requiring local validation.

## Supplemental Research

Supplemental sources used to position adjacent serving approaches:

- vLLM / PagedAttention: `https://arxiv.org/abs/2309.06180`. Used to distinguish KV memory management from token-level multi-model scale decisions.
- MuxServe: `https://proceedings.mlr.press/v235/duan24a.html`. Used to compare spatial-temporal multiplexing and multi-model colocation.
- DistServe: `https://arxiv.org/abs/2401.09670`. Used to contextualize prefill/decoding disaggregation and TTFT/TPOT framing.
- HydraServe: `https://arxiv.org/abs/2502.15524`. Used to contextualize serverless LLM cold-start acceleration and scale-up latency.

These sources are not primary evidence for the Aegaeon claims. They support the source-understanding comparison section and help avoid mispositioning Aegaeon as a replacement for all serving optimizations.

## Assumptions and Open Questions

Assumptions:

- The target team has a multi-model LLM serving environment where workload skew and burstiness may matter.
- The downstream PPT will be used for leadership architecture evaluation, not a paper reading group.
- The reader needs a bounded decision path: evaluate, retest, then consider adaptation.

Open questions for local evaluation:

- Does our model market have a comparable long-tail distribution?
- Do our top models have burst patterns that create reserved-capacity waste?
- What are our exact TTFT, TBT/TPOT, end-to-end latency, and SLO violation definitions?
- Can our runtime support safe token-boundary preemption?
- What is the measured KV cache movement/sync cost in our engine?
- Which engine lifecycle components can be reused or cached?
- What is our model switching latency budget relative to TBT?
- What fallback policy protects SLO if preemption or switching fails?
- What goodput/arrival-rate capacity improvement is meaningful enough to justify implementation work?

Claims that should be softened:

- Any statement implying the 82% GPU saving transfers to our stack.
- Any statement implying token-level pooling is superior for all multi-model serving.
- Any statement implying implementation is only a scheduler change.

## Approval Log

1. User selected audience option 1 with refinement: technical product / infrastructure leadership evaluating token-level GPU pooling adaptation. Baseline saved at `baselines/01-audience.md`.
2. Source-understanding HTML approved as basis for SCQA and storyline. User emphasized the Alibaba Cloud beta deployment boundary. Baseline saved at `baselines/01-source-understanding.md`.
3. User selected top-level summary option B: `先评估，再承诺收益`. Baseline saved at `baselines/01-audience-thesis.md`.
4. User selected 7 total pages including cover, summary, and contents. Baseline saved at `baselines/02-page-count.md`.
5. User approved table of contents order and four titles. Baseline saved at `baselines/02-table-of-contents.md`.
6. User approved Page 4 viewpoint layer. Baseline saved at `baselines/03-chapter-1-page-plan.md`.
7. User approved Page 5 viewpoint layer. Baseline saved at `baselines/03-chapter-2-page-plan.md`.
8. User approved Page 6 viewpoint layer. Baseline saved at `baselines/03-chapter-3-page-plan.md`.
9. User approved Page 7 viewpoint layer. Baseline saved at `baselines/03-chapter-4-page-plan.md`.
10. Consolidated page plan with content layer saved at `baselines/03-page-plan.md`.
11. Final approval bundle saved at `QA/approval_bundle.md` and passed `--approval-bundle-check`.
12. User approved final hard constraints and requested handoff writing plus PPT content brief QA.
