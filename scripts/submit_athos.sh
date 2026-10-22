cd ~/hpc-consluting-agent/athos
# scripts/run_cug_eval.sh \
#   --dataset-profile full \
#   --flow-profile lang_chroma_glm_5.3_flash_opt \
#   --experiment-id glm-5.3-flash_eval_hpc \
#   --aggregate-manifest ~/athos_clean/athos/athos/data/chroma/aggregates/manifests/athos_eval_bundle_20260318_derived_tickets_lt_20250901_v2.json \
#   --skip-scoring

./scripts/run_cug_eval.sh \
  --dataset-profile full \
  --flow-profile lang_chroma_glm_5.3_flash_opt \
  --experiment-id glm-5.3-flash_eval_hpc \
  --skip-execution \
  --judge-model llama_4_maverick \
  --judge-prompt-version rubric_v1