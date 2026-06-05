# Research Audit

## Research Frame

Task: prepare a PPT Deep Search content handoff for an internal model efficiency and serving strategy deck about TiDAR.

Target reader: model architecture / inference platform leaders evaluating whether hybrid diffusion-autoregressive decoding is worth tracking or replicating.

Reader's likely current belief:

- Diffusion language models have parallel decoding potential but quality and serving integration risks are high.
- Speculative decoding is the more familiar serving acceleration reference.
- Paper throughput numbers should not be treated as deployment gains without benchmark-scope and serving-assumption analysis.

Desired belief change:

- TiDAR is worth tracking and controlled replication.
- It is not ready to be treated as a deployment recommendation or proven serving cost/latency improvement.

Final use:

- Pre-PPT content brief for an internal model efficiency and serving strategy deck.

Primary source package:

- `forward-tests/ppt-deep-search\tidar-hitl\candidate\input\pdf_xml\tidar.pdf`
- `forward-tests/ppt-deep-search\tidar-hitl\candidate\input\pdf_xml\final\tidar.xml`
- `forward-tests/ppt-deep-search\tidar-hitl\candidate\input\pdf_xml\final\images\`

## Source Understanding

Approved source-understanding artifact:

- `docs/showcase/published-run`
- `docs/showcase/published-run`

Core approved understanding:

- TiDAR is a sequence-level hybrid architecture that drafts via diffusion and samples final outputs autoregressively within a single model forward.
- The differentiated architecture uses structured attention masks to let one forward verify tokens drafted from the previous step and pre-draft proposals for the next step.
- The paper's quality-throughput signal is strong enough for controlled replication.
- The paper's speedups are not deployment-ready serving gains.

What it solves:

- AR decoding quality and exact KV cache support are strong, but one-token-per-step decoding can be memory-bound and underuse GPU compute density.
- Diffusion language models offer parallel token generation, but parallel token independence can degrade quality.
- Speculative decoding can accelerate AR decoding, but weak or separate drafters and sequential verification limit the capacity / parallelism profile.
- TiDAR tries to use free token slots in memory-bound decoding to pre-draft more candidate tokens while protecting final outputs through AR sampling.

Distinctive versus similar approaches:

- Versus classic speculative decoding: TiDAR does not rely on a separate weak drafter.
- Versus EAGLE-3 / speculative heads: TiDAR uses diffusion pre-drafting and claims parallel-to-verification behavior; EAGLE-3 comparison needs weight-pairing caveat.
- Versus MTP: TiDAR is not just AR-adjacent multi-token prediction; it uses structured diffusion pre-drafting.
- Versus Block Diffusion / Dream / LLaDA: TiDAR borrows diffusion's parallelism while using AR sampling to protect quality.

Source-understanding approval boundary:

- `4.71x` / `5.91x` are paper-setting relative AR throughput speedups.
- They are not our serving收益, production QPS, tail latency, GPU utilization, or cost reduction.
- `batch size = 1`, `single H100`, long-context training cost, custom attention kernels, and scheduling algorithms must remain explicit replication/deployment assumptions.

## Executive Thesis

SCQA:

- Situation: model efficiency / serving teams need to evaluate new decoding architectures, but paper throughput metrics cannot be treated as platform gains.
- Complication: TiDAR reports AR-level quality with diffusion-style parallel drafting and 4.71x / 5.91x relative AR throughput speedup, but under paper-specific settings.
- Question: is TiDAR worth tracking or replicating, and what must be verified next?
- Answer: TiDAR is worth controlled replication, but not deployment recommendation; the deck should split architecture, benchmark scope, and serving assumptions.

Approved top-level summary page:

- 页面标题：架构有新意，收益待验证
- 标题说明：TiDAR 把 diffusion pre-draft 放进 AR sampling，但平台收益仍取决于本地 serving 栈
- 分析总结：
  - 架构：structured masks 让验旧草稿与预写新草稿并行
  - 实验：8B 平均 T/NFE 8.25，对 AR 报 5.91x speedup
  - 假设：free token slots 在高 batch 和长上下文下未证明

## Reader Cognitive Path

1. Start with the decision posture: controlled replication, not deployment.
2. Confirm that TiDAR has a real architecture distinction: single forward with AR sampling plus diffusion pre-drafting.
3. Inspect quality-throughput evidence without overstating production meaning.
4. Split baseline comparison by axis: AR quality reference, speculative serving-neighbor reference, diffusion parallelism reference.
5. Convert serving assumptions into replication gates.

## Pyramid Outline

Top-level answer:

- TiDAR's architecture is interesting and worth tracking, but serving benefits remain unverified.

Chapter 1:

- 先看机制: judge whether single-forward hybrid architecture is differentiated.

Chapter 2:

- 再拆证据: judge quality-throughput evidence and baseline comparisons separately.

Chapter 3:

- 最后验假设: judge which serving assumptions must pass before platform strategy.

## Chapter Logic

Chapter 1 / 先看机制:

- Page 4 explains why TiDAR is not generic multi-token decoding. Its decision role is to assess engineering replication value.

Chapter 2 / 再拆证据:

- Page 5 handles quality-throughput evidence only. Its decision role is to assess whether the paper signal is strong enough for replication.
- Page 6 handles baseline comparison only. Its decision role is to assess where the comparative advantage comes from and which comparisons should not be overread.

Chapter 3 / 最后验假设:

- Page 7 turns unresolved serving assumptions into replication gates.

## Page Logic Audit

Page 2:

- Role: answer-first summary.
- Supported claim: TiDAR is a controlled replication candidate, not deployment recommendation.
- Boundaries: paper speedups are relative AR throughput under paper settings.

Page 4:

- Role: mechanism differentiation.
- Supported chapter claim: single-forward hybrid architecture is worth understanding before judging metrics.
- Boundary: do not reduce TiDAR to generic multi-token prediction.

Page 5:

- Role: quality-throughput evidence.
- Supported chapter claim: paper evidence justifies replication, not deployment.
- Boundary: keep batch=1/single H100 and relative AR throughput wording visible.

Page 6:

- Role: baseline comparison.
- Supported chapter claim: compare TiDAR on three axes, not one generic benchmark summary.
- Boundary: do not claim universal superiority over speculative decoding.

Page 7:

- Role: replication gates.
- Supported chapter claim: serving value requires local validation of assumptions.
- Boundary: do not present production serving gains as proven.

## Claim Evidence Implication Table

| Claim | Evidence | Implication |
| --- | --- | --- |
| TiDAR's novelty is same-forward verification and next-step pre-drafting. | Figure 2 and Figure 3 show architecture and attention masks. | Replication must include mask/KV/proposal mechanics, not just score evaluation. |
| Paper quality-throughput signal is strong enough to replicate. | Abstract/conclusion report 4.71x / 5.91x; Table 2/3/4 show quality and ablation results. | Recommend controlled replication. |
| Speedups are not serving gains. | Benchmark scope states single H100, batch size 1; limitations discuss batch size, long context, system optimization. | Keep production benefit as unproven. |
| Baseline comparison must be axis-specific. | Table 1, Figure 4, Table 2, Table 3 compare AR, EAGLE-3/speculative, diffusion baselines. | Separate Page 5 evidence from Page 6 comparison. |
| Serving value depends on local stack integration. | Figure 1 free-token-slot profiling and limitations text about kernels/scheduling. | Create replication gates for batch, hardware, long context, kernels, scheduler. |

## Evidence Map

| Evidence ID | Source Locator | Evidence Type | Strength | Counterevidence / Uncertainty | PPT Relevance |
| --- | --- | --- | --- | --- | --- |
| S1 | `tidar.xml`, abstract / introduction / conclusion | source | strong | headline speedups can be overread without benchmark scope | support summary and Page 5 |
| F1 | Figure 1, `images/picture_002.png`, page 3 | source | strong for assumption | profiling only, not end-to-end serving | must use or summarize on Page 7 |
| F2 | Figure 2, `images/picture_003.png`, page 5 | source | strong | conceptual architecture still needs implementation-cost analysis | must use on Page 4 |
| F3 | Figure 3, `images/picture_004.png`, page 5 | source | strong | mask implementation cost not quantified | use or summarize on Page 4 |
| F4 | Figure 4, `images/picture_005.png`, page 7 | source | strong for paper benchmark | relative throughput under paper settings only | must use on Page 5 |
| T1 | Table 1, `images/table_001.png`, page 3 | source | medium-strong | table is paper-authored categorization | use/rebuild on Page 6 |
| T2 | Table 2, `images/table_002.png`, page 9 | source | strong | task mix may not match internal eval | use/summarize on Page 5 |
| T3 | Table 3, `images/table_003.png`, page 10 | source | medium-strong | likelihood comparison across diffusion models uses different evaluation methods | summarize on Page 5 or Page 6 |
| T4 | Table 4, `images/table_004.png`, page 11 | source | strong for decoding strategy ablation | not a production workload | use/rebuild on Page 5 |
| T5 | Table 5, `images/table_005.png`, page 12 | source | medium | masking ablation is narrower than full architecture proof | background for Page 4 / audit |

Key numeric claims:

- TiDAR 1.5B average T/NFE 7.45 and 4.71x relative AR throughput speedup: source, strong, abstract/conclusion.
- TiDAR 8B average T/NFE 8.25 and 5.91x relative AR throughput speedup: source, strong, abstract/conclusion.
- TiDAR Trust Diff 8B generative average 65.31% versus Qwen3 8B 68.09%: source, strong, Table 2.
- TiDAR 8B likelihood average 75.40% versus Qwen3 8B 74.25%: source, strong, Table 3.
- TiDAR 8 drafts Avg T/NFE 5.49 with HumanEval Avg 39.94%, MBPP Avg 52.13%, GSM8k 54.74%: source, strong, Table 4.

## Source Usage Policy

- Figure 1: original or summarized assumption visual. Must be described as profiling under Qwen3-32B, H100, batch size 1, Flash Attention 2.
- Figure 2: original visual on Page 4.
- Figure 3: original or summarized visual on Page 4.
- Figure 4: original visual on Page 5.
- Table 1: summarized/rebuilt comparison matrix on Page 6.
- Table 2: original or summarized on Page 5.
- Table 3: summarized on Page 5/Page 6.
- Table 4: original or rebuilt on Page 5.
- Table 5: background only unless mechanism detail needs more support.

## Supplemental Research

No external supplemental research was used. The final brief is based on the TiDAR paper package only.

## Assumptions and Open Questions

Assumptions:

- The deck's intended use remains internal strategy / pre-PPT content planning.
- The downstream PPT maker can decide visual layout, but must preserve source figure associations and approved page logic.
- The target reader prefers decision-oriented Chinese with English method/model/metric names retained.

Open questions for replication:

- Does the free-token-slot region exist under the team's production hardware, batch distribution, and serving scheduler?
- How do continuous batching, prefix caching, KV paging, and existing speculative mechanisms interact with TiDAR?
- Can mask slicing/reordering and proposal selection be implemented without unacceptable kernel or synchronization overhead?
- How does TiDAR behave under long-context workloads, given appended mask tokens in current training?
- Which EAGLE-3 or speculative comparator weights should be used for fair local replication?

## Approval Log

- Stage 1 audience approved: `baselines/01-audience.md`.
- Stage 1.5 source-understanding HTML approved: `baselines/01-source-understanding.md`.
- Stage 1.6 SCQA and summary page approved: `baselines/01-audience-thesis.md`.
- Stage 2 page count approved: `baselines/02-page-count.md`.
- Stage 2.5 table of contents approved: `baselines/02-table-of-contents.md`.
- Stage 3 chapter 1 Page 4 viewpoint approved: `baselines/03-chapter-1-page-plan.md`.
- Stage 3 chapter 2 Page 5 and Page 6 viewpoints approved: `baselines/03-chapter-2-page-plan.md`.
- Stage 3 chapter 3 Page 7 viewpoint approved: `baselines/03-chapter-3-page-plan.md`.
- Consolidated page plan saved: `baselines/03-page-plan.md`.
- Final hard-constraint approval bundle passed QA and was approved by user: `QA/approval_bundle.md`.
