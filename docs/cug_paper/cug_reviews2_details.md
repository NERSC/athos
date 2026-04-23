## Source

---

- Downloaded file: `pap143 Reviews Details.pdf`
- Submission: `pap143s2`
- Decision: **CUG Proceedings and ACM ICPS Accept**
- Paper: **An Agentic Toolkit and Comparative Study for HPC Operations and User Support**
- Contributors listed in review packet: Demeure, Ding, Farrell, Konate, Lei, Naylor
- Acceptance notice thread: [Bilel ACM ICPS acceptance](https://mail.google.com/mail/u/1/#all/19d9b4af8e3b7d60)

## Score Summary

---

| **Reviewer** | **rel** | **tech** | **orig** | **rec** |
| --- | --- | --- | --- | --- |
| Reviewer 5 | 3 | 3 | 3 | WEAK ACCEPT (3) |
| Reviewer 6 | 3 | 3 | 3 | ACCEPT (4) |
| Reviewer 7 | 5 | 4 | 5 | ACCEPT (4) |
| Reviewer 8 | 4 | 4 | 3 | WEAK ACCEPT (3) |
| **Average** | **3.8** | **3.5** | **3.5** | **3.5** |

## Cross-Cutting Feedback

---

- Overall reception is positive: reviewers consistently see the topic as timely and relevant to HPC centers.
- The most repeated weakness is **presentation clarity**, especially in Sections 3 and 4.
- Several reviewers want a clearer explanation of the **ATHOS architecture, guardrails, and operational constraints**.
- Multiple comments ask for more explanation of **why certain retrieval/framework/model results behave the way they do**, not just what the aggregate scores are.
- One reviewer explicitly asks for a clearer statement about **public availability of the software/materials**.
- Reviewer 6 contributed mostly **editorial and organization comments** that can be converted directly into a revision checklist.

## Likely Still Relevant After M4 Update

---

- Clarify architecture and deployment details beyond the list of open-source components.
- Explain resource management / guardrails / constraints for agent operation in HPC settings.
- Improve definitions and terminology for SRE-oriented, single-turn, and multi-turn cases.
- Tighten result-table naming and references so row/config names are used consistently.
- Reorganize Sections 3 to 5 for a more linear flow and better alignment with the tables/figures.
- Add a public-availability statement for code/materials if that is still the intent.
- Expand the discussion around why retrieval sometimes hurts quality and why effects differ by model/harness.

## Possibly Stale W.R.T. Post-Submission M4 Changes

---

- Comments about missing depth on retrieval behavior may be partially addressed by the newer M4-backed analysis and reruns.
- Any comments tied to exact figure readability, row names, or table references should be checked against the latest draft before actioning them verbatim.
- The concern that the paper does not go deep enough on whether centers should deploy such systems may be partly mitigated if the newer discussion/limitations text already strengthened the deployment guidance.

## Reviewer-Specific Notes

---

- Reviewer 5
    - Wants more deployable detail about ATHOS beyond tool names (for example resource consumption and guardrails).
    - Wants deeper explanation of retrieval degradations and model-specific sensitivity to added context.
    - Wants the judge rubric and task difficulty split explained more clearly, ideally with some human-judgment grounding on hard technical cases.
    - Main meta-point: useful preliminary study, but not yet deep enough on whether and how centers should deploy these frameworks.
- Reviewer 6
    - Main issue is readability and naming consistency in the results discussion.
    - Concrete editorial asks: define SRE-oriented, single-turn, and multi-turn; explain admin/policy exclusions and the Sept. 1, 2025 split; enumerate the four points in Section 5.5; standardize naming such as LangChain + Claude Sonnet; reference tables by number.
    - Also suggests related-work citations for ChatHPC / AskHPC-adjacent work and asks to mention external coding-agent configuration details.
- Reviewer 7
    - Strongly positive on relevance and breadth of Section 5 analysis.
    - Main weakness is exposition in Sections 3 and 4: too dense, insufficiently linear, and too reliant on prior familiarity with agent tooling.
    - Specifically asks for more grounding to Figures 1 and 2 and suggests moving Section 4.3 before 4.6.
    - Flags missing statement or citation about whether ATHOS software/materials are publicly available.
- Reviewer 8
    - Positive but brief: methods were explained in detail, results are interesting though somewhat underwhelming, and the work is still worth publishing.

## Suggested Revision Checklist

---

- Audit the latest M4 draft against these comments and mark each one as addressed, still relevant, or obsolete.
- Add a short explicit paragraph on ATHOS deployment constraints: guardrails, resource control, and why the paper focuses on evaluation rather than production automation.
- Add a direct explanation of the main negative retrieval findings and the role of excess or unstable context.
- Standardize config naming across tables, figures, and prose.
- Add definitions for SRE-oriented, single-turn, and multi-turn cases where first introduced.
- Revisit Section ordering so the architecture/eval flow is easier to follow.
- Add or confirm a statement on software/material availability.
- Treat Reviewer 6's line-level comments as a final editorial pass once the latest draft text is frozen.

## Provenance

---

- Related planning note: [CUG ATHOS paper plan](https://www.notion.so/CUG-ATHOS-paper-plan-306edaa853bf818d9c91c852aefc4725?pvs=21)
- Related submission note: [CUG 2026 ATHOS Abstract (Full Submission Version)](https://www.notion.so/CUG-2026-ATHOS-Abstract-Full-Submission-Version-306edaa853bf812498fbe34a4f195b2d?pvs=21)
- Related presentation task: [Prepare CUG 2026 Technical Session 6A presentation](https://www.notion.so/Prepare-CUG-2026-Technical-Session-6A-presentation-32dedaa853bf81e783c1c193c8c4b3f3?pvs=21)
