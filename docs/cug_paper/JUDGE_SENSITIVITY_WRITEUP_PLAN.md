# Judge Sensitivity Writeup Plan (Lightweight Supplemental)

This plan defines a compact, paper-friendly judge-sensitivity section using the three available judges:
- `gptoss` (stricter),
- `llama_4_maverick` (middle),
- `mistral_large_3` (more lenient).

The goal is to show trend robustness without a heavy methodological detour.

## Scope

Use paper-facing result artifacts already scored under all three judges:
- main table sources (`config/paper/cug_paper_table_sources.txt`),
- harness mini comparison (`results/cug_m3_var_20260311_231139` + external mini dirs),
- variance pair (`results/cug_m3_var_20260312_093435`, `results/cug_m3_var_20260312_130318`) as optional qualitative support.

## Output 1: Leniency Ladder (Table)

Purpose:
- Show calibration differences in absolute scores/pass rates.

Minimal content:
- rows: `gptoss`, `llama_4_maverick`, `mistral_large_3`
- columns:
  - overall `score_mean`,
  - overall `pass_rate`,
  - total `scored_count`,
  - total `skipped_count`.

Interpretation sentence:
- “Absolute calibration varies by judge; GPTOSS is strictest, Mistral most lenient, Maverick in between.”

## Output 2: Ranking Stability (Table)

Purpose:
- Show whether key comparative conclusions change with judge choice.

Minimal content:
- limit to the main paper configurations (the six LangChain rows; optionally include filesystem rows).
- for each judge:
  - per-config rank by `score_mean` (and optionally by `pass_rate`),
  - top-1 and bottom-1 consistency note.

Interpretation sentence:
- “Despite calibration shifts, rank ordering of key headline rows is largely stable.”

## Output 3: Delta View (Compact Table or Small Figure)

Purpose:
- Show size/direction of judge effects per configuration.

Recommended reference:
- use Maverick as center reference and show:
  - `Δ score_mean` vs Maverick,
  - `Δ pass_rate` vs Maverick,
  for GPTOSS and Mistral.

Interpretation sentence:
- “Judge choice shifts absolute values but preserves core direction-of-effect findings (e.g., optimized retrieval vs baseline).”

## Suggested Placement in Paper

- Main text: short subsection after main results or near limitations.
- Appendix (optional): detailed per-config delta table if space is tight.

## Target Length

- 1 short paragraph + 1 compact table in main text,
- optional second table in appendix.

## Writing Guardrails

- Do not over-claim inter-judge agreement.
- Emphasize:
  - calibration differences are expected,
  - robustness is about trend/ranking stability, not identical absolute values.
- Keep methods brief (same stored outputs rescored under fixed rubric prompt version).
