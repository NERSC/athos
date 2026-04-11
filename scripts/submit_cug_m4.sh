#!/bin/bash

EXP_ID=cug_m4
JUDGE=llama_4_maverick
MANIFEST=data/chroma/aggregates/manifests/athos_eval_bundle_20260318_derived_tickets_lt_20250901_v2.json

# Main results, full dataset

# gptoss main results
scripts/run_cug_eval.sh \
  --dataset-profile full \
  --flow-profile lang_chroma_gptoss \
  --judge-model "$JUDGE" \
  --aggregate-manifest "$MANIFEST" \
  --experiment-id "$EXP_ID"

scripts/run_cug_eval.sh \
  --dataset-profile full \
  --flow-profile lang_chroma_gptoss_opt \
  --judge-model "$JUDGE" \
  --aggregate-manifest "$MANIFEST" \
  --experiment-id "$EXP_ID"

scripts/run_cug_eval.sh \
  --dataset-profile full \
  --flow-profile lang_filesystem_gptoss \
  --judge-model "$JUDGE" \
  --experiment-id "$EXP_ID"

# sonnet main results
scripts/run_cug_eval.sh \
    --dataset-profile full \
    --flow-profile lang_chroma_sonnet \
    --judge-model "$JUDGE" \
    --aggregate-manifest "$MANIFEST" \
    --experiment-id "$EXP_ID"
scripts/run_cug_eval.sh \
    --dataset-profile full \
    --flow-profile lang_chroma_sonnet_opt \
    --judge-model "$JUDGE" \
    --aggregate-manifest "$MANIFEST" \
    --experiment-id "$EXP_ID"
scripts/run_cug_eval.sh \
    --dataset-profile full \
    --flow-profile lang_filesystem_sonnet \
    --judge-model "$JUDGE" \
    --experiment-id "$EXP_ID"

# Harness study
# GPTOSS
scripts/run_cug_eval.sh \
    --dataset-profile mini \
    --flow-profile lang_chroma_gptoss_opt \
    --run-count 1 \
    --experiment-id "${EXP_ID}_harness" \
    --judge-model "$JUDGE" \
    --aggregate-manifest "$MANIFEST"
scripts/run_cug_eval.sh \
    --dataset-profile mini \
    --flow-profile smol_chroma_gptoss \
    --run-count 1 \
    --experiment-id "${EXP_ID}_harness" \
    --judge-model "$JUDGE" \
    --aggregate-manifest "$MANIFEST"

# Variance study
# GPTOSS
scripts/run_cug_eval.sh \
    --dataset-profile mini \
    --flow-profile lang_chroma_gptoss_opt \
    --run-count 10 \
    --experiment-id "${EXP_ID}_var" \
    --judge-model "$JUDGE" \
    --aggregate-manifest "$MANIFEST"
# Sonnet partial runs
./scripts/run_cug_eval.sh \
    --dataset-profile mini \
    --flow-profile lang_chroma_sonnet_opt \
    --run-count 10 \
    --experiment-id "${EXP_ID}_var" \
    --judge-model "$JUDGE" \
    --aggregate-manifest "$MANIFEST"
