# Judge Sensitivity Plan: Llama-4-Maverick

This plan adds a third judge (`llama-4-maverick`) on top of existing `gptoss` and `mistral_large_3` judgments.
It is intentionally staged to maximize signal per token spend.

## Status Snapshot (2026-03-15)

Completed:
- Phase 1 complete (`results/cug_m3_var_20260311_231139`):
  - `scored=48`, `skipped=0`
- Phase 2 complete (external mini dirs):
  - `results/cug_codex_external_mini_20260313_232712`: `scored=12`, `skipped=0`
  - `results/cug_claude_external_mini_20260314`: `scored=12`, `skipped=0`
- Phase 3 complete (expanded optimized rows):
  - `results/cug_m3_full_gptoss_opt_20260311_013848`: `scored=265`, `skipped=14` (`skipped_execution_status` only)
  - `results/cug_m3_full_sonnet_opt_20260311_081645`: `scored=278`, `skipped=1` (`skipped_execution_status` only)

Observed so far:
- No `skipped_judge_error` in Phases 1-3.
- Ranking stability held on completed slices:
  - mini harness ranking unchanged across GPTOSS/Mistral/Maverick,
  - expanded optimized pair ordering (`sonnet_opt` > `gptoss_opt`) unchanged.
- Spend checkpoint:
  - pre-Phase-3 spend: `39.08108147`
  - post-Phase-3 spend: `39.46084594`
  - Phase-3 delta: `0.37976447` for 558 runs (~`0.00068`/run).

## Goal

- Check whether key conclusions remain stable with a third, non-overlapping judge.
- Prioritize ranking stability and direction-of-effect stability over exact metric matching.

## Preconditions

1. Confirm model availability in i2 API:

```bash
source ~/.bash_aliases
check_i2api_models | rg -i "llama|maverick"
```

2. Add a judge model alias in `config/paper/cug_m1.yaml` (if not already present), for example:

```yaml
  llama_4_maverick:
    description: "Llama 4 Maverick via AmSC i2 API"
    model_id: "llama-4-maverick"
    api_key: "${AMSC_I2_API_KEY}"
    api_base: "${AMSC_I2_API_URL}"
    temperature: 0.0
    max_tokens: 2048
```

3. Setup env:

```bash
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate athos
source ~/.bash_aliases
setup_i2api
```

## Run Order (Cost-Controlled)

### Phase 1: Mini ATHOS Harness Slice (48 runs)

Target:
- `results/cug_m3_var_20260311_231139`

Command:

```bash
d="results/cug_m3_var_20260311_231139"
jid="llama_4_maverick_rubric_v1_$(basename "$d")"

python evals/score_runs.py \
  --config config/paper/cug_m1.yaml \
  --runs-dir "$d" \
  --judge-model llama_4_maverick \
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
```

### Phase 2: External Mini Slice (24 runs)

Targets:
- `results/cug_codex_external_mini_20260313_232712`
- `results/cug_claude_external_mini_20260314`

Command:

```bash
for d in \
  results/cug_codex_external_mini_20260313_232712 \
  results/cug_claude_external_mini_20260314
do
  jid="llama_4_maverick_rubric_v1_$(basename "$d")"

  python evals/score_runs.py \
    --config config/paper/cug_m1.yaml \
    --runs-dir "$d" \
    --judge-model llama_4_maverick \
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

### Phase 3: Paper-Headline Expanded Chroma Opt Rows (558 runs)

Targets:
- `results/cug_m3_full_gptoss_opt_20260311_013848`
- `results/cug_m3_full_sonnet_opt_20260311_081645`

Command:

```bash
for d in \
  results/cug_m3_full_gptoss_opt_20260311_013848 \
  results/cug_m3_full_sonnet_opt_20260311_081645
do
  jid="llama_4_maverick_rubric_v1_$(basename "$d")"

  python evals/score_runs.py \
    --config config/paper/cug_m1.yaml \
    --runs-dir "$d" \
    --judge-model llama_4_maverick \
    --judge-id "$jid" \
    --judge-prompt-version rubric_v1 \
    --judge-max-attempts 5 \
    --judge-retry-delay-ms 1500 \
    --cases-dir data/ticket_cases \
    --qa-file evals/nersc_qa.v2.jsonl \
    --output "$d/judgments/${jid}.jsonl" \
    --skips-output "$d/judgments/${jid}.skips.jsonl"

  python evals/summarize_results.py \
    --runs-dir "$d" \
    --judgment-file "$d/judgments/${jid}.jsonl" \
    --output "$d/aggregates/summary.${jid}.json"
done
```

### Phase 4 (Optional): Full M2 Canonical (1116 runs)

Target:
- `results/cug_m2_canonical`

Run only if broader full-table Maverick swap is desired after the already-stable Phase 1-3 checks.

## Budget Guardrails

Before and after each phase:

```bash
check_i2api_usage
```

Recommended stop conditions:
- stop if spend increase exceeds planned budget for the phase,
- stop if `skipped_judge_error` rate exceeds ~2% and investigate retry/provider stability first.

## Comparison Checks

For each completed phase, compare:
- configuration ranking by `score_mean` and `pass_rate`,
- pairwise gap direction (e.g., Sonnet-opt vs GPTOSS-opt),
- failure visibility (`skipped_execution_status`) consistency.

High-signal outputs to include in paper note/appendix:
- “stable” if ordering and key qualitative claims are unchanged across all 3 judges,
- “sensitive” if ranking flips in headline rows or large gap-direction reversals appear.

## Remaining Work for Full Maverick Artifact Swap

To regenerate all paper tables/plots entirely with Maverick judgments, remaining scoring is:
- `results/cug_m2_canonical` (1116 runs)
- `results/cug_m3_20260313_080148` (279 runs)
- `results/cug_m3_fs_sonnet_stitched_20260314` (279 runs)
- `results/cug_m3_var_20260312_093435` (120 runs)
- `results/cug_m3_var_20260312_130318` (120 runs)

Total remaining: `1914` runs (after Phases 1-3).
