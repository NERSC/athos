# Truncation and Chunking Tradeoffs (Open Decision Note)

## Context

Current balanced ingestion uses:
- `max_comment_chars=12000`
- `max_work_note_chars=12000`
- `max_incident_chars=40000`

Observed full balanced run (`servicenow_tickets_balanced_v0_20260223`):
- `documents=25093`
- `truncated_comment_docs=928`
- `truncated_work_note_docs=42`
- `chunked_tickets=0`

Interpretation:
- We are capping discussion sections before the incident-level chunk trigger is reached.
- This keeps runtime/cost predictable, but can remove late-thread details.

## Problem Statement

Ticket resolution information often appears near the end of discussions. Current section-level truncation can:
- remove the resolution/fix text,
- preserve comments and work notes asymmetrically,
- distort chronology because sections are capped independently.

This creates risk for retrieval accuracy in ticket-resolution tasks.

## Why We Have Caps

Caps are not primarily about a hard Chroma limit. They are practical controls for:
- ingestion runtime,
- embedding cost,
- memory stability,
- retrieval quality degradation from giant log-heavy documents.

## Current Behavior (Important Detail)

Truncation is applied to the **flattened section aggregate**:
- all customer comments are flattened then capped as one block,
- all internal work notes are flattened then capped as one block.

This is not per-entry truncation.

## Options Under Consideration

## Option A: Keep current section caps (status quo)
- Pros:
  - Lowest ingestion cost and simplest behavior.
  - Stable document count.
- Cons:
  - Highest risk of dropping end-of-thread resolution.
  - Chronology can be imbalanced across sections.

## Option B: Increase section caps + keep incident chunking
- Pros:
  - More discussion preserved without changing architecture.
  - Simple incremental change.
- Cons:
  - Higher embedding cost.
  - Still section-asymmetric truncation if caps are hit.

## Option C: Remove/loosen section caps; rely on incident-level chunking
- Pros:
  - Stronger preservation of long-thread content.
  - Reduces probability of losing resolution text.
- Cons:
  - More chunks/documents and higher storage/query cost.
  - Requires careful chunk metadata and retrieval strategy.

## Option D: Chronological merged timeline + single shared budget
- Pros:
  - Preserves order between comments and work notes.
  - Avoids section-asymmetric truncation.
- Cons:
  - More implementation work than cap tuning.
  - Still a truncation policy decision unless combined with chunking.

## Option E: Chronological timeline chunking (with overlap)
- Pros:
  - Best preservation of full conversation flow and endings.
  - Natural fit for long-ticket retrieval.
- Cons:
  - Highest implementation and compute/storage complexity.
  - More complex retrieval/post-processing (re-group by incident).

## Suggested Evaluation Plan (Before Final Policy)

Run an A/B/C comparison on the same balanced source slice:

1. A: current policy (baseline).
2. B: raised caps (for example 24k/24k, same incident cap).
3. C: no section caps (or very high), rely on incident chunking.

Track:
- ingestion runtime,
- document count and chunked ticket count,
- truncation counts,
- retrieval quality on fixed smoke/eval query set,
- explicit “resolution recall” checks on known long-thread tickets.

## Decision Criteria

Choose the policy that best balances:
- resolution recall,
- retrieval precision,
- operational cost/runtime.

For CUG M1, if resolution recall is materially better, prefer a chunking-forward policy over aggressive section truncation.

## Open Questions

- Should we preserve head+tail when truncation is unavoidable?
- Should chunking happen on chronological windows with overlap?
- Should retrieval return top chunks then aggregate by incident before final answering?
