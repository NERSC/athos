# CUG Review Comment Resolution Plan

This plan turns the confirmed `pap143s2` reviewer packet into concrete camera-ready revision work. It is intentionally separate from the main paper execution plan so `PLAN.md` stays readable.

Primary references:

- [Full review packet transcript](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/cug_reviews2_full.md)
- [Existing synthesized notes](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/cug_reviews2_details.md)
- Main paper plan: [PLAN.md](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/PLAN.md)

## Status Snapshot (2026-04-22)

Paper repo: `/Users/sfarrell/Work/agentic-ops/athos_cug_2026_paper`

Pushed reviewer-response commits:

- `eac9b19` `Clarify toolkit design section flow`
- `fd1508f` `Improve experimental design section flow`
- `6e79aef` `Clarify benchmark terminology`
- `4d82447` `Explain ticket dataset filtering rationale`
- `ae8765f` `Add ATHOS availability statement`
- `bf034fb` `Clarify ATHOS deployment boundary`
- `907dddb` `Describe external coding-agent conditions`
- `463dfc9` `Use configuration-oriented result wording`

Manuscript changes completed so far:

- Section 3 now opens with a high-level execution-order overview and explicit figure grounding for the architecture and execution-flow figures.
- Section 4 now has a roadmap and a more linear order: experiment matrix, datasets/retrieval corpora, model configuration, tool ingestion, execution/scoring, reproducibility logging.
- Jargon cleanup removed unnecessary `single-turn`, replaced `SRE-oriented` with `site-reliability`, and uses `interactive multi-turn` where the future-work contrast matters.
- Ticket dataset filtering and the September 1, 2025 temporal split now include reviewer-requested rationale.
- The introduction now includes a safe open-source release intent and public/private artifact boundary.
- Section 3 now includes a production-readiness boundary and guardrails paragraph.
- Section 4 now describes the external coding-agent conditions as holistic standalone-CLI comparisons run outside ATHOS and imported into the ATHOS scoring pipeline.
- Manuscript section prose now avoids table-centric `row(s)` language in favor of `configurations`, `conditions`, and `systems`.

Current paper repo state after the last check: tracked files clean; untracked LaTeX build artifacts remain (`main.aux`, `main.bbl`, `main.log`, `main.pdf`, etc.).

Recommended next handoff tasks:

- Check whether ACM `shortauthors` is still needed in the rendered PDF; if the author header collides, add an appropriate `\renewcommand{\shortauthors}{...}`.
- Inspect Figure 3 / variance figure zero markers in the rendered PDF and adjust marker visibility if still hard to see.
- Decide whether to add the two related-work citations suggested by Reviewer 6 (Joslin et al. FAQ generation from support tickets; Bondapalli et al. AskHPC).
- Decide whether to include a human-audit result or only a future-work/limitation statement; if included, update the judge/rubric discussion accordingly.
- Do a final Section 5 transition pass around the "four practical operating points" subsection and ensure it does not read like an early section ending.
- Do a final naming/reference sweep for spacing around `LangChain + Claude Sonnet`, table-number references, and any remaining table-centric prose.

## Triage Summary

High-value comments to address in the paper:

- clarify ATHOS deployment boundaries, guardrails, and resource-control posture
- explain retrieval degradation and optimized retrieval improvements more directly
- improve readability and linearity in Sections 3 and 4
- standardize result-row naming and table/figure references
- define dataset/task terminology (`SRE-oriented`, `single-turn`, `multi-turn`)
- state software/material availability clearly
- add a brief human-validation note or appendix-backed evidence for judge reasonableness if feasible

Likely low-cost editorial fixes:

- enumerate the four points in Section 5.5
- explain the admin/policy exclusion rule
- explain the September 1, 2025 split
- standardize `LangChain + Claude Sonnet` formatting
- reference the main table by number instead of by name
- improve Figure 3 zero visibility if the figure remains in the same form
- use ACM `shortauthors` if the author header collision still exists

Probably not worth over-correcting:

- turning the paper into a deployment recommendation paper rather than an evaluation paper
- adding large new experiment tracks unless needed to support an already planned revision

## Proposed Document Changes

Recommended structure:

1. Keep [PLAN.md](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/PLAN.md) as the master execution/status document.
2. Keep [cug_reviews2_full.md](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/cug_reviews2_full.md) as the source-of-truth markdown transcript for the review packet.
3. Use this file as the working resolution checklist for comment closure.

This keeps raw source, synthesized notes, and action tracking separate.

## Resolution Matrix

### Reviewer 5

| Comment | Action | Status |
| --- | --- | --- |
| ATHOS deployment details are too thin; paper should discuss resource limits and guardrails. | Added a Section 3 deployment-boundary paragraph: ATHOS is evaluated as a prototyping/evaluation framework, uses read-only retrieval/diagnostic operations in this study, and production deployments require additional authorization, guardrails, human approval workflows, and safety controls. | addressed |
| Retrieval can hurt quality; explain why this happens and why effects differ by model. | Existing Section 5 already discusses unstable retrieval, excess context, model sensitivity, and a retrieval-driven failure example; still worth one final review for whether the explanation is strong enough. | partially addressed |
| Optimized retrieval variants help but paper does not explain how. | Section 4 now explains optimized variants as tightening active retrieval tool subset and retrieval-path wiring to reduce unnecessary context loading, avoid unstable tool behavior, and improve reliability. Section 5 also discusses token/latency effects. | mostly addressed |
| Judge rubric needs more explanation; hard technical cases may need human cross-check. | Judge sensitivity is in the manuscript, and local human-audit docs exist, but the manuscript does not yet include a completed human-audit result or a stronger rubric explanation. | open |
| Paper does not go far enough to answer whether centers should deploy such systems. | Section 3 now explicitly limits claims to evaluation/prototyping and says production deployment requires additional controls beyond those evaluated. | addressed |

### Reviewer 6

| Comment | Action | Status |
| --- | --- | --- |
| Results discussion uses inconsistent row names. | Manuscript sections now avoid `row(s)` wording and use `configurations`, `conditions`, or `systems`; final naming/reference sweep still recommended. | mostly addressed |
| Define `SRE-oriented`. | Replaced with `site-reliability` language in introduction, Section 4, and conclusion. | addressed |
| Add related-work citations for FAQ/ticket support work. | Review and add the cited SC'25 workshop papers if appropriate to the related work section. | open |
| Mention external coding-agent configuration details, not only LangChain configuration details. | Section 4 now describes E10 as holistic standalone-CLI coding-agent conditions run outside ATHOS on the same auxiliary prompts and frozen file-retrieval corpus, with read-only/reference-solution restrictions and imported scoring. | addressed |
| Define `single-turn`. | Removed unnecessary `single-turn` wording instead of adding a term definition. | addressed |
| Explain admin/policy exclusions. | Section 4 now frames exclusions around keeping the benchmark focused on user-support troubleshooting and excluding internal operations, administrative workflows, staff-initiated work, and automated system alerts. | addressed |
| Explain why Sept. 1, 2025 is the split date. | Section 4 now explains the cutoff as a pragmatic sample-size choice that leaves a sufficiently large recent candidate pool while retaining a larger pre-cutoff retrieval corpus, and notes temporal separation from retrieval-enabled agents. | addressed |
| Define `multi-turn`. | Kept only as `interactive multi-turn` in future-work wording; no formal definition needed. | addressed |
| `no-tool rows` wording is ambiguous. | Manuscript sections now avoid `row(s)` wording; `no-tool baselines` remains intentionally where appropriate. | addressed |
| Enumerate the four points in Section 5.5. | Section 5 currently introduces "four practical operating points" and then lists them as separate paragraphs; final transition/format check still recommended. | partially addressed |
| Section 5.5 feels like the section ending before more subsections follow. | Section 4 was reorganized; Section 5 still needs a final transition pass around the operating-points subsection. | open |
| Figure 3 zero values are hard to see. | Update figure styling if the figure remains; otherwise confirm the final figure already resolves this. | open |
| `LangChain+Claude Sonnet` and `SmolAgents + Claude Sonnet` formatting is inconsistent. | Some wording has been cleaned up, but a final naming/spacing sweep is still recommended. | partially addressed |
| Main table should be referenced by number. | Current manuscript generally uses `Table~\ref{...}`; final sweep still recommended to catch any name-based references. | mostly addressed |
| Author list collides with conference header. | Check rendered PDF; add ACM `shortauthors` if the collision still exists. | open |

### Reviewer 7

| Comment | Action | Status |
| --- | --- | --- |
| Sections 3 and 4 are dense and not linear enough. | Section 3 now starts with an execution-order overview; Section 4 now has a roadmap and reordered structure. | addressed |
| Section 3 needs more grounding to Figures 1 and 2. | Section 3 now explicitly references the architecture and execution-flow figures in the opening overview and FlowRunner discussion. | addressed |
| Section 4.3 should likely move before 4.6. | Section 4 was reorganized around experiment matrix, datasets/retrieval corpora, model configuration, tool ingestion, execution/scoring, and reproducibility logging. | addressed |
| Public availability of software/materials is unclear. | Introduction now states intent to release ATHOS as open-source software after removing site-specific configuration, credentials, and non-public operational data, with sensitive NERSC records/private corpora excluded. | addressed |

### Reviewer 8

| Comment | Action | Status |
| --- | --- | --- |
| Broadly positive; results are interesting but somewhat underwhelming. | No direct response required beyond making the interpretation clearer and keeping claims appropriately scoped. | acknowledged |

## Execution Order

### Pass 1: Low-risk editorial and clarity fixes

- standardize naming and formatting throughout the manuscript
- define key terms at first use
- add the policy/admin exclusion explanation
- add the September 1, 2025 split explanation
- enumerate Section 5.5 points
- convert loose table references to numbered references
- add figure callouts where Sections 3 and 4 currently feel under-grounded

### Pass 2: Substantive but bounded content additions

- add deployment-boundary and guardrails paragraph
- add retrieval-behavior interpretation paragraph
- add optimized-retrieval explanation
- add external coding-agent configuration summary
- add software/material availability statement

### Pass 3: Structure pass

- review and potentially reorder subsections in Sections 3 and 4
- tighten transitions in Section 5 so intermediate subsections do not read like conclusions

### Pass 4: Optional validation upgrade

- if feasible before camera-ready freeze, complete the human audit mini-study and cite the agreement summary
- if not feasible, keep the audit as planned future work and avoid overpromising

## Recommended Scope Boundary

What I think is reasonable:

- treat these reviews primarily as a paper-clarity and framing revision, not as a mandate for major new experiments
- leverage already-completed M4 and judge-sensitivity work to answer the retrieval and methodology comments
- treat the human audit as the only optional new evidence item worth doing if time allows

Alternative if time is tight:

- close all editorial, structural, and framing comments
- defer the human audit to future work
- explicitly state the production-readiness boundary and availability status rather than trying to expand scope

## Closure Criteria

This comment-resolution pass is done when:

- every reviewer comment is marked addressed, intentionally deferred, or obsolete against the latest manuscript
- the latest draft has a clear deployment-boundary statement
- the latest draft has a clear software/material availability statement
- Sections 3 and 4 read linearly enough without assuming too much prior agent-tooling knowledge
- the results section uses one consistent naming/reference scheme
