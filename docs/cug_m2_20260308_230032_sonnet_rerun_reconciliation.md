# CUG M2 Sonnet Chroma Rerun Reconciliation

Date: 2026-03-10 UTC  
Experiment: `cug_m2_20260308_230032`

Compared configs:
- Original: `cug_lang_chroma_sonnet__claude_sonnet__7034e2f0` (`run_index=0`)
- Rerun (new API/model mapping): `cug_lang_chroma_sonnet__claude_sonnet__19c4421d` (`run_index=1`)

## 1) Full outcome breakdown (new rerun config)

Source set size: 156 runs
- `nersc_qa.v2`: 123
- `ticket_cases_failed_cug_m2_20260308_230032_cug_lang_chroma_sonnet__claude_sonnet__7034e2f0`: 33

Execution status:
- `success`: 146
- `execution_error`: 10

Error types:
- `ToolException`: 10

Notable:
- Previous `budget_exceeded` errors are gone in this rerun config.
- Remaining failures are tool-side collection lookup failures (`Collection ... does not exist`).

## 2) Ticket-case recovery (explicit retry subset)

From original config (`run_index=0`):
- Failed `ticket_cases`: 33

From rerun config (`run_index=1`, subset dataset):
- Retried ticket cases: 33
- Recovered to success: 33/33
- Still failing: 0

Result: ticket-case failures were fully recovered.

## 3) QA comparison (old vs rerun)

For `nersc_qa.v2` (123 cases):
- Original success: 0/123
- Rerun success: 113/123

Transition counts (old -> rerun):
- `execution_error -> success`: 113
- `execution_error -> execution_error`: 10

Remaining 10 QA failures:
- `0909352b2e3c` (`hpc_docs` missing)
- `0bcceba69383` (`hpc_docs` missing)
- `634553712685` (`hpc_docs` missing)
- `bb7c6d297dae` (`hpc_docs` missing)
- `bcb67c3aef60` (`hpc_docs` missing)
- `cc2712bf11fb` (`hpc_docs` missing)
- `ccf1fa2015cb` (`hpc_docs` missing)
- `d04263d9c2ea` (`hpc_docs` missing)
- `f5c761ed3572` (`hpc_knowledge_base` missing)
- `fcd139f0dafc` (`hpc_docs` missing)

## 4) Recommended stitched view for scoring

For the original 279-case target set (`ticket_cases` + `nersc_qa.v2`):
- Prefer rerun (`run_index=1`, config `19c4421d`) when rerun status is success.
- Fall back to original (`run_index=0`, config `7034e2f0`) otherwise.

Projected stitched execution success:
- 269 / 279 = 96.42%

This is the highest-quality combined execution set from currently available artifacts.

## 5) Practical note on dataset ID mismatch

The rerun ticket subset dataset ID is:
- `ticket_cases_failed_cug_m2_20260308_230032_cug_lang_chroma_sonnet__claude_sonnet__7034e2f0`

This differs from canonical `ticket_cases`.  
If desired, normalize these 33 records (dataset_id only) before final scoring/reporting to simplify downstream grouping.
