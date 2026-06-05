# Research Audit

## Research Frame

Task: Build a PPT-ready content brief for an internal technical evaluation deck about `Stochastic KV Routing: Enabling Adaptive Depth-Wise Cache Sharing`.

Workspace root:

`docs/showcase/published-run`

Primary source package:

- `forward-tests/ppt-deep-search\stochastic-kv-routing-hitl\candidate\input\pdf_xml\final\stochastic-kv-routing.xml`
- `forward-tests/ppt-deep-search\stochastic-kv-routing-hitl\candidate\input\pdf_xml\final\images\`
- `forward-tests/ppt-deep-search\stochastic-kv-routing-hitl\candidate\input\pdf_xml\source.json`

Audience:

LLM serving / inference infra 工程负责人和技术产品决策者.

Desired belief change:

The audience should believe depth-wise KV sharing is worth controlled reproduction because it is orthogonal to token eviction and KV quantization, but it should not be treated as a direct production rollout recommendation until training/fine-tuning cost, TTFT/throughput impact, quality transfer, and local serving backend behavior are verified.

Final use:

Internal technical evaluation deck pre-brief. Chinese decision tone; English method names, model names, dataset names, and metrics preserved.

## Source Understanding

Approved HTML review:

`docs/showcase/published-run`

Approved report data:

`docs/showcase/published-run`

Source understanding approved on 2026-06-03:

- R-CLA / stochastic KV routing is a layer/depth-axis KV cache optimization route.
- It should not be framed as replacing token eviction or KV quantization.
- It has strong enough capacity and QA-retention signals to justify controlled reproduction.
- It does not provide enough evidence for direct production rollout.
- The main unresolved items are training/fine-tuning cost, local model-family transfer, serving backend behavior, TTFT/throughput, and interaction with existing compression routes.

Important primary source observations:

- Abstract and introduction: KV cache scales with batch size, sequence length, and model depth; R-CLA proposes random cross-layer attention to make depth-wise cache sharing robust.
- Figure 4: training uses stochastic KV routing; inference uses deterministic sharing groups.
- Table 4: Qwen3-8B-like, 36 layers, 8 KV heads, bfloat16, single 80GB GPU, batch size 1. At 8K input, g=1 KV cache 1170MB, g=4 KV cache 293MB; TTFT 297ms vs 286ms; throughput 34.0 vs 41.6 tok/s.
- Table 5: at 8,192-token context, batch size 16 is OOM for g=1 and completes for g=4 with peak memory 60,306MB, KV cache 4,643MB, TTFT 4,696ms, throughput 8.0 tok/s.
- Table 2: R-CLA improves QA F1 under cache retention pressure across Llama-3.1-8B, Mistral-7B, and Qwen3-8B, especially at 50% and 25% retention.
- Table 3: R-CLA is more robust than fixed CLA@2 / CLA@4 variants across retention levels on Llama-3.1-8B QA tasks.
- Table 1 and Appendix figures: R-CLA can train stably in the reported setup, but fine-tuning can learn more slowly; training/fine-tuning behavior remains a reproduction concern.
- Limitations section: method requires training resources; posthoc or adapter-like versions remain future work; experiments do not cover overtraining; MoE not evaluated; fine-tuning evaluation focuses on QA tasks; composition with temporal eviction and KV quantization is left to future work.

## Executive Thesis

Approved thesis:

`先复测，再谈上线`

R-CLA is worth controlled reproduction because it adds a layer/depth-axis capacity experiment beyond token/time, bit, and head-axis KV optimizations. The strongest source-backed signals are approximately 4x KV cache reduction under g=4 and batch scaling from OOM to runnable at 8K context. However, the current evidence is insufficient for direct rollout because quality transfer, training cost, local backend TTFT/throughput, and interaction with existing serving optimizations are not yet proven.

## Reader Cognitive Path

1. Start with route classification: R-CLA is not another token eviction or KV quantization method.
2. Explain mechanism: stochastic training makes deterministic inference sharing plausible.
3. Show why it deserves reproduction: capacity and QA-retention evidence are meaningful.
4. Stop overclaiming: the deck must end with local reproduction gates, not an implied rollout path.

## Pyramid Outline

Top-level summary page:

- Page 2: 先复测，再谈上线.

Chapter claims:

- 先看优化轴: R-CLA is a distinct layer/depth-axis candidate.
- 再看可行性: Mechanism and source data justify controlled reproduction.
- 最后看门槛: Production discussion requires local quality, cost, and serving proof.

Page map:

- Page 1: cover.
- Page 2: top-level summary.
- Page 3: contents.
- Page 4: route orthogonality.
- Page 5: R-CLA mechanism.
- Page 6: capacity and quality signals.
- Page 7: local reproduction gates.

## Chapter Logic

Chapter 1 `先看优化轴`:

- Purpose: Prevent the reader from judging R-CLA as a replacement for token eviction or KV quantization.
- Supported by: primary paper related-work framing and supplemental comparison sources.
- Page: Page 4.

Chapter 2 `再看可行性`:

- Purpose: Explain how R-CLA works and why the source data justifies reproduction.
- Supported by: Figure 4, Table 4, Table 5, Table 2, Table 3.
- Pages: Page 5 and Page 6.

Chapter 3 `最后看门槛`:

- Purpose: Preserve the "not direct rollout" boundary and turn it into reproduction requirements.
- Supported by: primary paper limitations, fine-tuning dynamics, and source-data scope.
- Page: Page 7.

## Page Logic Audit

Page 2:

- Role: Answer first and preview the full logic.
- Visible title: 先复测，再谈上线.
- Supported chapter claims: route orthogonality, engineering signal, validation gates.
- Boundary: do not imply reproduction guarantees production rollout.

Page 4:

- Role: Establish optimization-axis taxonomy.
- Visible title: 不是替代，是补轴.
- Supported chapter claim: R-CLA is layer/depth-axis work.
- Boundary: do not describe H2O/KIVI/GQA as failed competitors.

Page 5:

- Role: Explain mechanism and cost shift.
- Visible title: 随机训练，确定共享.
- Supported chapter claim: random training enables deterministic sharing.
- Boundary: do not call R-CLA a pure runtime switch.

Page 6:

- Role: Present strongest source-backed reproduction signal.
- Visible title: 信号够复测.
- Supported chapter claim: capacity and quality data justify controlled reproduction.
- Boundary: do not treat single-GPU or QA-retention data as production proof.

Page 7:

- Role: Convert caution into local reproduction gates.
- Visible title: 过三关再上线.
- Supported chapter claim: production discussion requires quality, cost, and service proof.
- Boundary: do not turn this into an implementation roadmap.

## Claim Evidence Implication Table

| Claim | Evidence | Implication |
| --- | --- | --- |
| R-CLA is a layer/depth-axis route, not a replacement for token or bit compression. | Paper introduction and related work distinguish temporal eviction/compression, architectural improvements, and depth-wise redundancy; supplemental H2O/KIVI/GQA/CLA/PyramidKV sources clarify axes. | Page 4 should frame R-CLA as an orthogonal candidate and possible combination item. |
| R-CLA changes model adaptation, not only runtime behavior. | Figure 4 and method text: during training, layers randomly choose own or previous-layer KV; during inference, fixed deterministic sharing is used. | Page 5 should explain training/fine-tuning cost and version-management implications. |
| Capacity evidence is strong enough for reproduction. | Table 4: 8K KV cache 1170MB -> 293MB; Table 5: 8K batch 16 g=1 OOM, g=4 runnable. | Page 6 should foreground these numbers. |
| Quality evidence supports "not obviously collapsing" under retention pressure. | Table 2 and Table 3 show R-CLA outperforms Base or fixed CLA@k across many low-retention QA settings. | Page 6 can say quality signal supports reproduction, while avoiding production-quality claims. |
| Direct rollout is not justified. | Limitations mention training resources, no MoE evaluation, QA-focused fine-tuning, and future work for combination with temporal eviction / KV quantization. | Page 7 should define local reproduction gates. |

## Evidence Map

| ID | Source locator | Evidence type | Strength | Counterpoint or uncertainty | PPT relevance |
| --- | --- | --- | --- | --- | --- |
| S1 | `stochastic-kv-routing.xml`, abstract/introduction/method/limitations | source | strong | XML extraction should be checked against images for tables/figures | background and audit only |
| F4 | `images/picture_005.png`, Figure 4 | source | strong | Mechanism diagram does not prove serving performance | must use as source figure on Page 5 |
| T1 | `images/table_001.png`, Table 1 | source | medium | Pre-training stability is Qwen3-1.7B-style and limited setup | audit support for training cost discussion |
| T2 | `images/table_002.png`, Table 2 | source | strong for QA retention; medium for production quality | QA tasks are proxies, absolute F1 can remain low | may use/summarize on Page 6 |
| T3 | `images/table_003.png`, Table 3 | source | medium-strong | Llama-3.1-8B only for ablation | optional Page 6 support |
| T4 | `images/table_004.png`, Table 4 | source | strong for single-GPU capacity | not production scheduler or SLO | must use or rebuild on Page 6 |
| T5 | `images/table_005.png`, Table 5 | source | strong for batch scaling in paper setup | no multi-tenant serving proof | must use on Page 6 or Summary Page |
| R1 | H2O arXiv:2306.14048 | supplemental paper | medium for axis comparison | not used to judge R-CLA quality | Page 4 comparison context |
| R2 | KIVI arXiv:2402.02750 | supplemental paper | medium for axis comparison | not used to judge R-CLA quality | Page 4 comparison context |
| R3 | GQA arXiv:2305.13245 | supplemental paper | medium for head-axis comparison | model-architecture context only | Page 4 comparison context |
| R4 | Cross-layer Attention Sharing arXiv:2408.01890 | supplemental paper | medium for adjacent layer-axis context | not the same as stochastic routing | audit and Page 4/5 context |
| R5 | PyramidKV arXiv:2406.02069 | supplemental paper | medium for adjacent layer-aware token budget | not equivalent to depth-wise KV source sharing | Page 4 context |

## Source Usage Policy

- Figure 4 / `picture_005.png`: Use original source image for Page 5 mechanism. Do not redraw as if it were original if simplified.
- Table 4 / `table_004.png`: Use original source image or reconstruct a simple bar/table from the exact values. If reconstructed, keep original nearby in the brief or audit.
- Table 5 / `table_005.png`: Use original source image for batch scaling; especially the batch 16 OOM vs runnable row.
- Table 2 / `table_002.png`: Use original table or summarized numeric callouts. Avoid implying production quality.
- Table 3 / `table_003.png`: Optional support for R-CLA vs fixed CLA@k robustness.
- Page 4 method-axis map: agent-authored explanatory diagram is allowed, but it should be labeled as a simplified comparison in downstream work, not a paper figure.
- Page 7 reproduction-gate table: agent-authored synthesis from approved constraints; not a paper table.

## Supplemental Research

Supplemental sources used for comparison context:

- H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models, arXiv:2306.14048. Used for token/time-axis comparison.
- KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache, arXiv:2402.02750. Used for bit/representation-axis comparison.
- GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints, arXiv:2305.13245 / EMNLP 2023. Used for head-axis comparison and GQA/MQA distinction.
- Cross-layer Attention Sharing for Large Language Models, arXiv:2408.01890. Used as adjacent layer/depth-axis comparison.
- PyramidKV: Dynamic KV Cache Compression based on Pyramidal Information Funneling, arXiv:2406.02069. Used to distinguish layer-aware token budget from depth-wise KV source sharing.

These sources are not used to override the primary paper's results; they only help define the comparison frame.

## Assumptions and Open Questions

Assumptions:

- The downstream PPT maker can create a cover page from metadata; `ppt_content_brief.md` does not need a Page 1 content block.
- The deck is an internal evaluation pre-brief, not a final production rollout proposal.
- The source image paths remain accessible on the same machine.

Open questions for reproduction:

- Which local model family should be used first: Qwen-like 7B/8B, internal serving model, or a smaller controlled model?
- Which task suite best captures internal long-context quality and business risk?
- What p values and group sizes should be tested beyond p=0.6 and g=4?
- How does R-CLA interact with existing paged KV, continuous batching, CUDA graph, speculative decoding, quantized KV, and token eviction stack?
- Can a lighter adapter or posthoc method approximate R-CLA benefits without full fine-tuning?

Anti-overclaim notes:

- Do not promise production SLO from Table 4/5.
- Do not promise combined benefits with token eviction or KV quantization.
- Do not infer MoE performance; the paper does not evaluate MoE.
- Do not infer broad production quality from QA retention datasets.

## Approval Log

- 2026-06-03: User selected target audience option 1 and expanded audience, belief change, deck use, tone, terminology, and page-count preference.
- 2026-06-03: Stage 1 audience baseline saved at `baselines/01-audience.md`.
- 2026-06-03: Source-understanding HTML review and report data created under `review/`.
- 2026-06-03: `python scripts/validate_html_review_data.py <report-data.json>` passed.
- 2026-06-03: `python scripts/validate_html_review.py <source_understanding_review.html>` passed.
- 2026-06-03: User approved Stage 1.5 source understanding.
- 2026-06-03: Stage 1.5 source-understanding baseline saved at `baselines/01-source-understanding.md`.
- 2026-06-03: User approved SCQA and selected/revised top-level summary page to `先复测，再谈上线`.
- 2026-06-03: Stage 1.6 thesis baseline saved at `baselines/01-audience-thesis.md`.
- 2026-06-03: User approved 7 total PPT pages with Page 1 cover, Page 2 summary, Page 3 contents, Page 4-7 content pages.
- 2026-06-03: Page-count baseline saved at `baselines/02-page-count.md`.
- 2026-06-03: User approved table of contents.
- 2026-06-03: TOC baseline saved at `baselines/02-table-of-contents.md`.
- 2026-06-03: User approved Page 4 viewpoint; chapter 1 baseline saved.
- 2026-06-03: User approved Page 5 and Page 6 viewpoints; chapter 2 baseline saved.
- 2026-06-03: User approved Page 7 and overall Page 4-7 viewpoints; chapter 3 baseline saved.
- 2026-06-03: Consolidated page-plan baseline saved at `baselines/03-page-plan.md`.
- 2026-06-03: Final hard constraints approval bundle saved at `QA/approval_bundle.md`; `--approval-bundle-check` passed.
- 2026-06-03: User approved final landing and requested final `ppt_content_brief.md`, `research_audit.md`, and brief QA with expected pages 7.
