# Human Audit Review Instructions

This document describes how to complete the human-validation audit for the CUG paper.

Primary files:

- [HUMAN_AUDIT_PLAN.md](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/HUMAN_AUDIT_PLAN.md)
- [human_audit_candidate_sample.csv](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/human_audit_candidate_sample.csv)
- [human_audit_review_sheet.csv](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/human_audit_review_sheet.csv)
- [human_audit_review_packet.md](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/human_audit_review_packet.md)

## Goal

For each sampled run, determine whether a human reviewer agrees with the stored automated judgment outcome and whether the judge rationale is reasonable.

The review is intentionally narrow:

- assess the run's answer quality against the benchmark reference
- compare human pass/fail to automated pass/fail
- note disagreement types when they occur

This is not a full re-annotation of the benchmark.

## What To Review Per Row

For each row in the worksheet:

1. Open the generated review packet:
- `docs/cug_paper/human_audit_review_packet.md`
2. Navigate to the matching row/case in the packet.
3. Read:
- the user prompt
- the model response
- the reference answer
- the automated judgment rationale
4. Decide whether a human would mark the response as `pass` or `fail` under the same general benchmark standard.
5. Judge whether the stored automated rationale is:
- `reasonable`
- `partially_reasonable`
- `unreasonable`
6. If human and automated pass/fail differ, assign a `disagreement_type`.

The packet is intended to eliminate the need to open raw `run.json` files manually during normal review. The `run_path` remains in the worksheet for traceability and spot-checking.

## Worksheet Columns

The worksheet includes these blank columns to fill:

- `reviewer`
- `human_pass`
- `agreement`
- `judge_rationale_quality`
- `disagreement_type`
- `notes`

Allowed values:

- `human_pass`: `pass`, `fail`
- `agreement`: `agree`, `disagree`
- `judge_rationale_quality`: `reasonable`, `partially_reasonable`, `unreasonable`
- `disagreement_type`:
  - `threshold/borderline`
  - `partial_credit`
  - `wrong_root_cause`
  - `over-penalized_detail`
  - `over-credited_plausible_answer`
  - `execution_skip_handling`
  - `other`

## Review Heuristics

Use these heuristics consistently:

- Mark `pass` when the answer identifies the correct root cause or gives materially correct guidance, even if wording differs from the reference.
- Mark `fail` when the answer misses the actual issue, recommends the wrong remediation, or is too incomplete to be operationally useful.
- For borderline cases near score 80, focus on whether the answer would actually be acceptable to a consultant or user in practice.
- For execution skips, ask whether the automated `fail` treatment is appropriate for the paper's use of pass/fail as an end-to-end system metric.

## Suggested Workflow

Recommended order:

1. Review all `borderline` rows first.
2. Review all `fail_or_skip` rows second.
3. Review `clear_pass` rows last.

This surfaces the most informative judgment-validity cases earlier.

## Suggested Summary After Review

After the worksheet is complete, compute:

- overall agreement rate
- agreement by dataset (`qa`, `ticket`)
- agreement by stratum (`clear_pass`, `borderline`, `fail_or_skip`)
- count of each disagreement type

The paper writeup should emphasize whether disagreements are concentrated in borderline and partial-credit cases rather than clear passes and clear failures.
