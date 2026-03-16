#!/usr/bin/env bash

set -euo pipefail

# Phase 1 of llama-4-maverick judge sensitivity:
# - target: results/cug_m3_var_20260311_231139 (48 runs total)
# - datasets: evals/simple_qa.jsonl + evals/test_cases

CONFIG="${CONFIG:-config/paper/cug_m1.yaml}"
RUNS_DIR="${RUNS_DIR:-results/cug_m3_var_20260311_231139}"
JUDGE_MODEL="${JUDGE_MODEL:-llama_4_maverick}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
JUDGE_MAX_ATTEMPTS="${JUDGE_MAX_ATTEMPTS:-5}"
JUDGE_RETRY_DELAY_MS="${JUDGE_RETRY_DELAY_MS:-1500}"

if [[ ! -d "${RUNS_DIR}" ]]; then
  echo "ERROR: runs directory not found: ${RUNS_DIR}" >&2
  exit 2
fi

label="$(basename "${RUNS_DIR}")"
judge_id="${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}_${label}"
judgments_out="${RUNS_DIR}/judgments/${judge_id}.jsonl"
skips_out="${RUNS_DIR}/judgments/${judge_id}.skips.jsonl"
summary_out="${RUNS_DIR}/aggregates/summary.${judge_id}.json"

echo "== Llama Maverick judge sensitivity (Phase 1)"
echo "   runs_dir: ${RUNS_DIR}"
echo "   judge_model: ${JUDGE_MODEL}"
echo "   judge_id: ${judge_id}"
echo

python evals/score_runs.py \
  --config "${CONFIG}" \
  --runs-dir "${RUNS_DIR}" \
  --judge-model "${JUDGE_MODEL}" \
  --judge-id "${judge_id}" \
  --judge-prompt-version "${JUDGE_PROMPT_VERSION}" \
  --judge-max-attempts "${JUDGE_MAX_ATTEMPTS}" \
  --judge-retry-delay-ms "${JUDGE_RETRY_DELAY_MS}" \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --output "${judgments_out}" \
  --skips-output "${skips_out}"

python evals/summarize_results.py \
  --runs-dir "${RUNS_DIR}" \
  --judgment-file "${judgments_out}" \
  --output "${summary_out}"

echo
echo "Done."
echo "  judgments: ${judgments_out}"
echo "  skips:     ${skips_out}"
echo "  summary:   ${summary_out}"
