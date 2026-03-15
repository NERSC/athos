# Judge Swap Runbook (Mistral Large 3)

This runbook records the completed Mistral judge swap and the reproducible commands for rerendering paper artifacts.

## Status (2026-03-15)

### Completed rescoring

- Main paper-scope runs are rescored with `mistral_large_3`:
  - `results/cug_m2_canonical`
  - `results/cug_m3_full_gptoss_opt_20260311_013848`
  - `results/cug_m3_full_sonnet_opt_20260311_081645`
  - `results/cug_m3_20260313_080148`
  - `results/cug_m3_fs_sonnet_stitched_20260314`
  - `results/cug_codex_external_mini_20260313_232712`
  - `results/cug_claude_external_mini_20260314`
- Skipped-judge rerun pass was applied for the above via `scripts/rerun_skipped_judge_errors.sh`.
- Remaining variance/harness run dirs are now rescored with `mistral_large_3`:
  - `results/cug_m3_var_20260311_231139` (`skipped=0`)
  - `results/cug_m3_var_20260312_093435` (`skipped=3`, execution-status only)
  - `results/cug_m3_var_20260312_130318` (`skipped=0`)

### Completed paper updates

- Regenerated main per-config table (`tables/cug_results_per_config.tex`) from Mistral summaries.
- Regenerated harness comparison table (`tables/cug_harness_comparison.tex`) from Mistral summaries.
- Regenerated variance figures (`figures/cug_variance_*_by_case.pdf`) from Mistral judgments.
- Updated manuscript narrative in `../athos_cug_2026_paper/main.tex`:
  - judge identity references now point to Mistral judge usage,
  - stale GPT-OSS-judge-era numeric claims were updated to match current tables.
- Updated wrapper defaults so paper regeneration no longer requires extensive env overrides.

### Remaining work

1. Build paper PDF and run final manuscript sanity check.
2. Optional follow-on sensitivity run: `llama-4-maverick` on mini datasets first (budget-gated).

## 0) Environment Setup

Run from ATHOS repo root:

```bash
cd /Users/sfarrell/Work/agentic-ops/athos
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate athos
source ~/.bash_aliases
setup_i2api
```

Optional budget check:

```bash
check_i2api_usage
```

## 1) Optional: Rerun/Repair Rescoring

The paper-scope rescoring is already complete for the main results, harness/variance dirs, and external mini baselines.
Use this only if an artifact needs repair or if you intentionally want to rerun:

- `results/cug_m3_var_20260311_231139`
- `results/cug_m3_var_20260312_093435`
- `results/cug_m3_var_20260312_130318`

Run:

```bash
for d in \
  results/cug_m3_var_20260311_231139 \
  results/cug_m3_var_20260312_093435 \
  results/cug_m3_var_20260312_130318
do
  label="$(basename "$d")"
  jid="mistral_large_3_rubric_v1_${label}"
  echo "== scoring $d (judge_id=$jid)"

  python evals/score_runs.py \
    --config config/paper/cug_m1.yaml \
    --runs-dir "$d" \
    --judge-model mistral_large_3 \
    --judge-id "$jid" \
    --judge-prompt-version rubric_v1 \
    --judge-max-attempts 5 \
    --judge-retry-delay-ms 1500 \
    --cases-dir evals/test_cases \
    --qa-file evals/simple_qa.jsonl \
    --output "$d/judgments/${jid}.jsonl" \
    --skips-output "$d/judgments/${jid}.skips.jsonl"

  python evals/summarize_results.py \
    --runs-dir "$d" \
    --judgment-file "$d/judgments/${jid}.jsonl" \
    --output "$d/aggregates/summary.${jid}.json"
done
```

Optional judge-error retry pass (if needed):

```bash
./scripts/rerun_skipped_judge_errors.sh
```

## 2) Update Main Per-Config Paper Table

Default wrapper behavior now targets paper-ready Mistral output:
- `ALLOW_MIXED_JUDGES=0`
- `JUDGE_MODEL_FILTER=mistral_large_3`
- output path: `../athos_cug_2026_paper/tables/cug_results_per_config.tex`

Run:

```bash
./scripts/render_cug_paper_table.sh
```

Notes:
- `scripts/render_cug_paper_table.sh` supports judge filters:
  - `JUDGE_ID_FILTER`
  - `JUDGE_MODEL_FILTER`
  - `JUDGE_PROMPT_VERSION_FILTER`
- Use `ALLOW_MIXED_JUDGES=0` with filter(s) to avoid mixed-judge aggregation.

## 3) Update Harness Comparison Table

Default wrapper behavior now points to the Mistral summary artifacts and paper output path.

```bash
./scripts/render_cug_harness_comparison_table.sh
```

## 4) Update Variance Figures

Default wrapper behavior now points to the Mistral judgment artifacts and paper figure output path.

```bash
./scripts/render_cug_variance_case_plots.sh
```

If Matplotlib cache permissions are noisy in this execution context, run:

```bash
MPLCONFIGDIR=/tmp/mplconfig ./scripts/render_cug_variance_case_plots.sh
```

## 5) Update Paper Text References (Only If Needed)

In `../athos_cug_2026_paper/main.tex`, verify/update:

- Judge description text (should reference the Mistral judge setup).
- Any explicit score/pass/fail values quoted in:
  - main per-config results narrative,
  - harness comparison narrative,
  - variance narrative (if figures are regenerated under Mistral).

## 6) Build and Verify Paper

```bash
cd /Users/sfarrell/Work/agentic-ops/athos_cug_2026_paper
latexmk -pdf main.tex
```

Recommended verification:
- `tables/cug_results_per_config.tex` compiles and matches mistral summaries.
- `tables/cug_harness_comparison.tex` reflects mistral ATHOS+external rows.
- variance figure PDFs match intended judge choice.

Quick verification command:

```bash
python3 - <<'PY'
import json
from pathlib import Path

paths = sorted(Path("results").glob("**/summary.mistral_large_3_rubric_v1_*.json"))
print("mistral_summary_files", len(paths))
for p in paths:
    d = json.loads(p.read_text())
    skip = 0
    judge_skip = 0
    for row in d.get("aggregates", []):
        skip += row.get("skipped_count", 0)
        judge_skip += row.get("skipped_by_reason", {}).get("skipped_judge_error", 0)
    print(f"{p}: skipped={skip}, skipped_judge_error={judge_skip}")
PY
```
