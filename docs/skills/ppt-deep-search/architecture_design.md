# Architecture Design

This is the development-time architecture document for `ppt-deep-search`. It explains the repository as a behavior contract for agents, not merely a set of prompts.

`SKILL.md` is runtime guidance for a candidate agent doing human-in-the-loop source research and PPT content-brief planning. This document is for maintainers and coding agents changing the repository.

## Architectural Goal

The repository turns source packages into a source-grounded, human-approved `ppt_content_brief.md` and `research_audit.md`.

Two invariants define the system:

1. Human-in-the-loop storyline decisions, source evidence, and downstream PPT copy are separate artifacts.
2. Runtime instructions, reference contracts, forward-test orchestration, and QA checks must stay consistent so agent behavior is predictable.

## Logical Architecture Elements

```text
+----------------------------------------------------------------------------------+
| L1 Runtime Contract                                                               |
|                                                                                  |
|  SKILL.md tells the candidate agent how to run HITL source understanding,         |
|  SCQA, page planning, final approval, and handoff writing.                       |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| L2 Reference Contracts                                                            |
|                                                                                  |
|  references/*.md define pyramid rules, PPT brief format, audit format,           |
|  HTML review standards, and reusable HTML review patterns.                       |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| L3 Review Surface                                                                 |
|                                                                                  |
|  The temporary source-understanding HTML helps the human inspect evidence,        |
|  comparison context, visual explanations, citations, and boundaries before        |
|  approving storyline work.                                                       |
|  Webpage evidence is captured first through Codex Browser/browser-use into        |
|  local text, image, screenshot, and manifest artifacts consumed by the review.    |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| L4 Handoff Artifacts                                                              |
|                                                                                  |
|  ppt_content_brief.md is downstream-facing PPT copy. research_audit.md owns      |
|  source locators, evidence boundaries, internal reasoning, and approvals.         |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| L5 Forward Tests                                                                  |
|                                                                                  |
|  forward-tests/* define candidate inputs and judge-only rubrics. The main agent   |
|  orchestrates an isolated child-agent run and writes judgment.md.                 |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| L6 Verification                                                                   |
|                                                                                  |
|  scripts/validate_ppt_content_brief.py validates final handoff structure.         |
|  scripts/validate_html_review.py validates the temporary HTML review surface.     |
|  verify_dependencies.py checks the repo contract and standard-library tooling.    |
+----------------------------------------------------------------------------------+
```

## Runtime Contract

Owned by:

- `SKILL.md`

Responsibilities:

- define the HITL sequence: audience, source understanding, SCQA, page count, TOC, page viewpoint layers, final hard constraints, handoff writing;
- tell the candidate agent when to create the temporary HTML review page;
- keep downstream PPT rendering details out of `ppt_content_brief.md`.

Constraints:

- `SKILL.md` should not carry development-time rationale that belongs in this document.
- If runtime behavior changes, update reference contracts and QA checks in the same change.
- A forward run must test the runtime contract through an isolated child agent, not the main thread.

## Reference Contracts

Owned by:

- `references/pyramid-principle.md`
- `references/ppt-content-brief-format.md`
- `references/research-audit-format.md`
- `references/html-review-surface.md`
- `references/html-review-data-model.md`
- `references/html-review-report-kit.md`
- `references/html-review-pattern-library.md`

Responsibilities:

- define what good output means independently of any one run;
- keep navigation logic separate from visible persuasive headings;
- keep source-grounding and citations auditable without polluting visible report prose;
- define local reusable data contracts, report blocks, and patterns instead of depending on external skill source at runtime.

Constraints:

- A reference contract must not merely say "borrow from another skill." Borrowed behavior must be rewritten into repo-local standards or patterns.
- New visible-report requirements should have a matching check in `scripts/validate_html_review.py` whenever practical.
- New downstream brief requirements should have a matching check in `scripts/validate_ppt_content_brief.py` whenever practical.

## HTML Review Surface

Owned by:

- candidate agent output under `<workspace-root>/review/`, where `workspace-root` is `.tmp/ppt-deep-search/<task>/` by default or an explicit output directory such as `.tmp/forward-tests/<case>/<run>/`
- `references/html-review-surface.md`
- `references/html-review-data-model.md`
- `references/html-review-report-kit.md`
- `references/html-review-pattern-library.md`
- `scripts/validate_html_review.py`
- `scripts/serve_html_review.py`

Responsibilities:

- help the human judge whether the agent understands the issue before approving SCQA and page planning;
- for webpage sources, consume local Codex Browser/browser-use evidence packages rather than live remote URLs or hotlinked images;
- use fixed logical labels for side navigation when useful;
- use claim-like, topic-specific body headings for persuasion;
- pair reconstructed visuals with original evidence and clickable citations when reconstruction is used.

Constraints:

- Body headings must not merely be outline labels such as `问题为什么重要`.
- Side navigation may use fixed logical labels because it serves wayfinding.
- Reconstructed charts must expose source data, original evidence, and citation anchors.
- Webpage citations and webpage images displayed in the report must map to local browser-use evidence assets through `report-data.json`.
- Internal labels such as `needs_verification`, `agent-chart`, and `QA` belong in audit records, not visible prose.

## Handoff Artifacts

Owned by:

- `<workspace-root>/ppt_content_brief.md`
- `<workspace-root>/research_audit.md`
- `<workspace-root>` defaults to `.tmp/ppt-deep-search/<task>/` and may be an explicit forward-run directory such as `.tmp/forward-tests/<case>/<run>/`

Responsibilities:

- `ppt_content_brief.md` contains PPT-ready titles, subtitles, analysis summaries, body material, image references, and notes;
- `research_audit.md` contains evidence maps, source locators, usage policy, approvals, open questions, and boundary reasoning.

Constraints:

- Downstream PPT copy must not contain internal audit fields or rendering implementation fields.
- Source images may use absolute local paths only as Markdown image references under `参考图片`.
- Every approved viewpoint layer must be preserved in the final brief.

## Forward Tests

Owned by:

- `AGENTS.md`
- `forward-tests/ppt-deep-search/README.md`
- case `main-agent-prompt.md`, `candidate/`, and `judge/`

Responsibilities:

- validate the skill through a clean child-agent run;
- keep judge-only files and main-agent theories away from the candidate child;
- simulate realistic stakeholder approvals and corrections;
- write `judgment.md` for every completed run.

Constraints:

- Do not fork full main-agent context into the child.
- Do not coach the child with expected fixes, prior failures, rubric criteria, or the main agent's validation hypothesis.
- If the child asks for approval on defective output, the main agent must request a revision rather than approve.
- If the run is contaminated, mark it invalid instead of treating it as evidence.

## Verification

Owned by:

- `scripts/validate_html_review.py`
- `scripts/validate_ppt_content_brief.py`
- `verify_dependencies.py`

Responsibilities:

- turn recurring failure modes into executable gates;
- keep checks standard-library-only unless a deliberate dependency is approved;
- provide concise error messages that tell the agent what to fix.

Constraints:

- QA scripts should validate hard hygiene and contract failures, not judge research truth, enforce a single report style, or replace editorial judgment.
- Forward judgment still requires human/main-agent review against the case rubric.
- Dependency verification must fail when required scripts or references are missing.
