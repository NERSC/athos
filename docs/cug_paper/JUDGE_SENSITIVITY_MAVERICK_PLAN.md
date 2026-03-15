# Judge Sensitivity Plan: Llama-4-Maverick

This plan adds a third judge (`llama-4-maverick`) on top of existing `gptoss` and `mistral_large_3` judgments.
It is intentionally staged to maximize signal per token spend.

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

Run only if Phase 1-3 indicates potentially material judge-dependent shifts.

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
