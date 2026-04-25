# Human Audit Plan for CUG Paper

This note defines a lightweight human-validation audit for the paper's rubric-based evaluation results.

## Goal

Verify that the automated Llama 4 Maverick rubric judgments used in the main paper are directionally consistent with human review on a stratified sample of evaluated runs.

The audit is intended to answer a narrow paper-validity question:

- If a human reads the prompt, model answer, and reference answer, do they generally agree with the automated pass/fail outcome?
- When disagreement occurs, is it concentrated in borderline or partial-credit cases rather than obvious failures?
- Are execution skips and unscorable outputs being treated reasonably by the automated pipeline?

This is not intended to replace the main automated evaluation pipeline or become a second benchmark. It is a spot-check for validity.

## Recommended Audit Size

Use a 48-item audit set.

Rationale:

- 48 is large enough to span all eight paper configurations.
- 48 is still small enough to review in one or two focused sessions.
- The sample can be balanced across datasets and outcome strata.

## Stratification

Sample exactly 6 items per main paper configuration:

- 3 from NERSC Q&A
- 3 from ticket troubleshooting

Within each dataset slice, use these three strata:

- `clear_pass`: an obvious high-scoring pass
- `borderline`: a judged run near the pass threshold
- `fail_or_skip`: either an execution skip/unscorable run, or the clearest available fail

This yields:

- 8 configurations
- 2 datasets per configuration
- 3 strata per dataset
- total = 48 reviewed runs

This design gives direct coverage of:

- both task families
- all eight rows in the paper's main table
- both strong and weak systems
- both content failures and execution failures
- threshold sensitivity around the fixed pass cutoff

## What Reviewers Should Score

For each sampled run, record:

1. `human_pass`
- `pass`
- `fail`

2. `judge_pass`
- taken directly from the stored judgment record

3. `agreement`
- `agree`
- `disagree`

4. `judge_rationale_quality`
- `reasonable`
- `partially_reasonable`
- `unreasonable`

5. `disagreement_type` when applicable
- `threshold/borderline`
- `partial_credit`
- `wrong_root_cause`
- `over-penalized_detail`
- `over-credited_plausible_answer`
- `execution_skip_handling`
- `other`

6. `notes`
- short free text

## Suggested Reporting in the Paper

Once the audit is complete, the paper can report:

- overall human vs automated pass/fail agreement
- agreement by dataset (`Q&A` vs `Tickets`)
- agreement by outcome stratum (`clear_pass`, `borderline`, `fail_or_skip`)
- a short qualitative summary of disagreement categories

The most useful expected result is not perfect agreement. The most useful result is:

- high agreement on clear passes and clear failures
- disagreement concentrated near the threshold or in partial-credit cases

## Candidate Sample Manifest

The initial 48-item candidate sample is stored in:

- [human_audit_candidate_sample.csv](/Users/sfarrell/Work/agentic-ops/athos/docs/cug_paper/human_audit_candidate_sample.csv)

The manifest was selected from the paper's actual evaluation rows:

- no-tool base rows from `results/cug_m2_canonical`
- retrieval rows from `results/cug_m4`

## Execution Notes

Practical review workflow:

1. For each manifest row, open the referenced `run.json`.
2. Read the user prompt and model output.
3. Read the corresponding reference solution:
- `evals/nersc_qa.v2.jsonl` for Q&A items
- `evals/test_cases/<case_id>/solution.md` for hand-authored troubleshooting cases
- ticket benchmark reference artifacts for curated ticket cases
4. Compare the human decision to the stored judge decision.
5. Record disagreement category when needed.

If time is constrained, the 48-item set can be reviewed in two passes:

- first pass: all `borderline` and `fail_or_skip` items
- second pass: `clear_pass` items

That still preserves the most informative cases first.
