# Judge Swap Runbook (Mistral Large 3)

This runbook is ordered to prioritize **finishing rescoring first**, then updating paper artifacts.

## Handoff Status (2026-03-15)

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

### Remaining work (for next agent)

1. Regenerate paper table artifacts from Mistral summaries.
2. Regenerate variance figures from Mistral judgments.
3. Update `../athos_cug_2026_paper/main.tex` text values and judge-description language.
4. Build paper PDF and sanity-check all updated table/figure references.

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

## 1) Finish Remaining Rescoring

The paper-scope rescoring is complete for the main results and external mini baselines.
Remaining judge-dependent artifacts are the harness/variance run dirs:

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

Render Mistral-only table using existing wrapper and canonical source manifest:

```bash
JUDGE_MODEL_FILTER=mistral_large_3 \
ALLOW_MIXED_JUDGES=0 \
TABLE_OUT=/Users/sfarrell/Work/agentic-ops/athos_cug_2026_paper/tables/cug_results_per_config.tex \
./scripts/render_cug_paper_table.sh
```

Notes:
- `scripts/render_cug_paper_table.sh` supports judge filters:
  - `JUDGE_ID_FILTER`
  - `JUDGE_MODEL_FILTER`
  - `JUDGE_PROMPT_VERSION_FILTER`
- Use `ALLOW_MIXED_JUDGES=0` with filter(s) to avoid mixed-judge aggregation.

## 3) Update Harness Comparison Table

Use Mistral summaries for:
- ATHOS harness: `cug_m3_var_20260311_231139`
- Codex external mini
- Claude external mini

```bash
ATHOS_SUMMARY=results/cug_m3_var_20260311_231139/aggregates/summary.mistral_large_3_rubric_v1_cug_m3_var_20260311_231139.json \
CODEX_SUMMARY=results/cug_codex_external_mini_20260313_232712/aggregates/summary.mistral_large_3_rubric_v1_cug_codex_external_mini_20260313_232712.json \
CLAUDE_SUMMARY=results/cug_claude_external_mini_20260314/aggregates/summary.mistral_large_3_rubric_v1_cug_claude_external_mini_20260314.json \
OUTPUT_TEX=/Users/sfarrell/Work/agentic-ops/athos_cug_2026_paper/tables/cug_harness_comparison.tex \
./scripts/render_cug_harness_comparison_table.sh
```

## 4) Update Variance Figures (If Swapping Judge for Figures Too)

Render with Mistral judgments for the two 10x repeated-run dirs:

```bash
GPTOSS_JUDGMENTS=results/cug_m3_var_20260312_093435/judgments/mistral_large_3_rubric_v1_cug_m3_var_20260312_093435.jsonl \
SONNET_JUDGMENTS=results/cug_m3_var_20260312_130318/judgments/mistral_large_3_rubric_v1_cug_m3_var_20260312_130318.jsonl \
OUTPUT_DIR=/Users/sfarrell/Work/agentic-ops/athos_cug_2026_paper/figures \
./scripts/render_cug_variance_case_plots.sh
```

## 5) Update Paper Text References

In `../athos_cug_2026_paper/main.tex`, update:

- Judge description text (currently references GPT-OSS rubric judge in main-table paragraph).
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
