# Research Audit

## Research Frame

Task: create a PPT-ready content brief for an internal architecture evaluation deck on whether RTX Spark should be treated as a new Windows local personal-agent PC platform category or mostly a marketing/spec update.

Workspace root: `docs/showcase/published-run`

Target reader: technical architecture / AI engineering leaders.

Reader's initial uncertainty: whether RTX Spark is truly a new local personal-agent PC platform category, or mainly a high-TOPS AI PC refresh framed by marketing.

Desired belief change: RTX Spark should enter architecture evaluation as the anchor of a Windows local personal-agent stack, but official wording and Chinese media paraphrases must be kept separate, and official specs must not be treated as mature-category proof.

Final artifact: total 6-page internal architecture evaluation deck content brief, including cover and table of contents.

## Source Understanding

Approved source-understanding judgment: RTX Spark is best interpreted as an anchor of a Windows local personal-agent stack, not simply a high-TOPS AI PC. The strongest basis is the combination of NVIDIA official wording, Microsoft-side unified-stack confirmation, RTX Spark silicon/memory claims, Windows security primitives, NVIDIA OpenShell policy/runtime routing, and the CUDA/RTX local AI ecosystem story.

Approved source-understanding HTML:

- `docs/showcase/published-run`
- `docs/showcase/published-run`

Source discovery map:

- `docs/showcase/published-run`

Browser/web-article-capture source packages:

- NVIDIA Newsroom press release: `docs/showcase/published-run`
- NVIDIA RTX Spark product page: `docs/showcase/published-run`
- NVIDIA Blog: `docs/showcase/published-run`
- Microsoft Build Live: `docs/showcase/published-run`
- NVIDIA GTC Taipei keynote page: `docs/showcase/published-run`

Evidence mirror paths used by report-data:

- `docs/showcase/published-run`
- `docs/showcase/published-run`
- `docs/showcase/published-run`
- `docs/showcase/published-run`
- `docs/showcase/published-run`
- `docs/showcase/published-run`
- `docs/showcase/published-run`
- `docs/showcase/published-run`
- `docs/showcase/published-run`

QA status before approval:

- `python web-article-capture/scripts/validate_capture_package.py <run-output>/sources/web --require-images always`: passed.
- `python scripts/validate_web_evidence_package.py <run-output>/review/report-data.json --require-images always --min-image-sources 1`: passed.
- `python scripts/validate_html_review_data.py <run-output>/review/report-data.json`: passed.
- `python scripts/validate_html_review.py <run-output>/review/source_understanding_review.html`: passed.
- Pollution keyword scan over `sources/web/*/source.md`: no hits after cleanup.

## Executive Thesis

RTX Spark should be framed as a Windows local personal-agent stack anchor. It combines hardware, memory, CUDA/RTX software ecosystem, Microsoft Windows security primitives, and NVIDIA OpenShell policy/runtime routing. It is not enough to describe it as a high-TOPS AI PC, because that misses the OS/runtime control problem that personal agents introduce on a user's primary device.

The deck must preserve a strong but bounded decision: evaluate it as a platform direction; do not call it a proven category, a procurement recommendation, or an official Chinese product name.

## Reader Cognitive Path

1. Name the object precisely: official wording is personal-agent Windows PC / unified accelerated computing stack; Chinese media phrases are paraphrases.
2. Reframe the evaluation unit: RTX Spark is not only silicon; it is silicon plus Windows trust layer, OpenShell, CUDA/RTX ecosystem, and local-agent workflows.
3. Separate signal from proof: official announcement, partner intent, and local inference optimization justify architecture evaluation, but not procurement or mature-category language.
4. Convert the story into validation gates: benchmark local workflows, evaluate security and policy controls, test power/stability, and verify supply/procurement terms.

## Pyramid Outline

Top-level summary: `先按平台看`.

Chapter claim 1: `先正名` — official wording and Chinese paraphrase must be separated before platform judgment.

Chapter claim 2: `看平台` — RTX Spark's meaningful signal is the combination of silicon, Windows trust layer, OpenShell, and CUDA/RTX ecosystem.

Chapter claim 3: `定门槛` — current evidence supports architecture evaluation, but the missing proof must be benchmarked and reviewed internally.

## Chapter Logic

`先正名` supports the top-level claim by preventing a category error. If the deck starts from Chinese media phrasing, it may overclaim. If it starts from official wording, it can make a stronger but more precise platform judgment.

`看平台` supports the top-level claim by showing why a pure TOPS comparison is insufficient. Personal agents need compute, memory, policy, identity, containment, and privacy routing.

`定门槛` supports the top-level claim by turning the interpretation into architecture action. It recommends evaluation gates, not procurement.

## Page Logic Audit

| Page | Role | Approved visible viewpoint | Supported chapter claim | Boundary |
| --- | --- | --- | --- | --- |
| Page 2 | Top-level summary | `先按平台看` | RTX Spark should be evaluated as a platform anchor | Do not call Chinese media wording official or category maturity proven |
| Page 4 | Naming boundary | `先正名再判断` | `先正名` | Official wording and Chinese paraphrase must remain separate |
| Page 5 | Platform mechanism | `平台信号已成形` | `看平台` | Security/runtime claims remain evaluation targets, not solved assurances |
| Page 6 | Evaluation gates | `先评估不采购` | `定门槛` | No procurement, standardization, or mature-category conclusion |

## Claim Evidence Implication Table

| Claim | Evidence | Implication |
| --- | --- | --- |
| RTX Spark is better evaluated as platform anchor than high-TOPS AI PC | NVIDIA says world's first Windows PCs purpose-built for personal agents; Microsoft says unified accelerated computing stack with RTX Spark Windows PCs and DGX Station for Windows | Deck title and summary should use platform language, not pure spec comparison |
| Chinese `Agent 原生电脑` is a paraphrase, not official product name | Official sources use English wording around personal agents and Windows PCs; source request itself notes Chinese title is media paraphrase | Page 4 must prevent naming inflation |
| Hardware is necessary but insufficient | NVIDIA lists 1 PFLOP FP4, up to 128GB unified memory, 120B-parameter LLMs, up to 1M tokens context; product page positions agents, AI development, creation, gaming | Page 5 should combine silicon with OS/runtime/economy, not isolate specs |
| Windows trust layer and OpenShell are central to the platform story | NVIDIA Newsroom and Blog describe identity, containment, policy, end-to-end security capabilities, OpenShell policy, privacy routing, and local/cloud routing | Architecture leaders should assess policy/control surfaces and security model |
| Current evidence supports evaluation, not procurement | Sources are official announcements, partner statements, product pages, local inference optimization chart, and Microsoft live blog; no independent workflow benchmark or supply/procurement validation | Page 6 should recommend benchmark/security/supply gates |

## Evidence Map

| Evidence id | Source | Locator | Key extracted facts | Type | Strength | PPT relevance |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | NVIDIA Newsroom press release | `sources/web/nvidia-news-windows-pcs-agents/source.md`, News Summary and Purpose-Built sections | world’s first Windows PCs purpose-built for personal agents; 1 petaflop AI performance; up to 128GB unified memory; Windows security primitives; OpenShell; fall availability | source | strong | Must use for official wording and boundary |
| R2 | NVIDIA RTX Spark product page | `sources/web/nvidia-rtx-spark-product/source.md`, Superchip and Agents sections | 6,144 cores; 20-core CPU; 1 Petaflop; 128GB memory; agents work alongside user; CUDA stack | source | strong | Use for platform/mechanism page and original images |
| R3 | NVIDIA Blog | `sources/web/nvidia-blog-rtx-ai-garage/source.md`, Local Agentic AI and llama.cpp sections | OpenShell on Windows; identity/policy/privacy routing; llama.cpp up to 2x / 1.6x optimization; DGX Spark relation | source | medium-strong | Use for platform and evaluation gates |
| R4 | Microsoft Build Live | `sources/web/microsoft-build-live-blog-4927/source.md`, NVIDIA/Microsoft unified stack, Surface Dev Box, Windows AI APIs | unified accelerated computing stack; RTX Spark Windows PCs; DGX Station for Windows; Surface RTX Spark Dev Box; FCC boundary | source | strong | Use for Microsoft-side confirmation and procurement boundary |
| R5 | NVIDIA GTC Taipei keynote page | `sources/web/nvidia-gtc-taipei-keynote/source.md` | June 1 Taipei keynote context and program schedule | source | medium | Background only unless event context is needed |

## Source Usage Policy

| Source/asset | Local path | Usage policy | Notes |
| --- | --- | --- | --- |
| RTX Spark agent workflow image | `review/assets/rtx-spark-agent-workflow.jpg` | original | Use to show product-page personal-agent scene |
| RTX Spark developer stack image | `review/assets/rtx-spark-developer-stack.jpg` | original | Use to support CUDA/RTX development stack framing |
| llama.cpp performance chart | `review/assets/llamacpp-performance.png` | original | Use as local inference optimization signal; must state RTX 5090/llama.cpp condition |
| Surface RTX Spark Dev Box image | `review/assets/surface-rtx-spark-dev-box.png` | original | Use as Microsoft-side developer-local compute signal; not supply proof |
| NVIDIA Newsroom full-page screenshot | `review/assets/nvidia-news-full-page.png` | audit / optional original context | Prefer audit use; only place in PPT if official headline context is needed |

## Supplemental Research

No non-official external supplemental research was used in the final storyline. All cited web material came from NVIDIA or Microsoft official pages captured through Codex in-app Browser / web-article-capture.

## Assumptions and Open Questions

Assumptions:

- The deck will be consumed by technical architecture / AI engineering leaders, not broad consumer or investment audiences.
- The downstream PPT skill can use the content brief to create Page 1 cover from metadata.
- The deck should remain architecture-evaluation oriented, not procurement oriented.

Open questions for follow-up:

- What exact local personal-agent workflows should be used for internal benchmarks?
- What are the detailed APIs and policy objects for Windows security primitives and NVIDIA OpenShell?
- Which RTX Spark devices, including Surface RTX Spark Dev Box or OEM systems, are actually procurable in the target region and time window?
- What are realistic power, thermal, sleep/wake, and sustained workload characteristics under local agent pipelines?
- How should local/cloud routing be audited when queries may include sensitive files or user context?

## Approval Log

| Stage | Status | Artifact |
| --- | --- | --- |
| Stage 1 audience | Approved | `baselines/01-audience.md` |
| Stage 1.5 source understanding | Initially rejected for capture pollution, revised, then approved | `baselines/015-source-understanding.md` |
| SCQA and summary page | Approved with candidate A `先按平台看` | `baselines/02-scqa-summary.md` |
| Page count | Approved: total 6 pages including cover and contents | `baselines/025-page-count.md` |
| Table of contents | Approved | `baselines/026-table-of-contents.md` |
| Page 4 viewpoint | Approved | `baselines/03-chapter-1-page-plan.md` |
| Page 5 viewpoint | Approved | `baselines/03-chapter-2-page-plan.md` |
| Page 6 viewpoint | Approved | `baselines/03-chapter-3-page-plan.md` |
| Consolidated page plan | Approved through chapter-by-chapter approvals | `baselines/03-page-plan.md` |
| Final hard constraints | Approved after approval bundle QA | `QA/approval_bundle.md` |

Final handoff files:

- `ppt_content_brief.md`
- `research_audit.md`
