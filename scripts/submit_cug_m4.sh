#!/bin/bash

EXP_ID=cug_m4
JUDGE=llama_4_maverick
MANIFEST=data/chroma/aggregates/manifests/athos_eval_bundle_20260318_derived_tickets_lt_20250901_v2.json

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
