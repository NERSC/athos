#!/usr/bin/env bash

set -euo pipefail

# Minimal end-to-end smoke test for eval pipeline v2.
# Override these with env vars if needed.
FLOW_NAME="${FLOW_NAME:-lang_chat}"
JUDGE_MODEL="${JUDGE_MODEL:-cborg_coder}"
JUDGE_ID="${JUDGE_ID:-${JUDGE_MODEL}_rubric_v1}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
RUN_COUNT="${RUN_COUNT:-1}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
LOGS_ROOT="${LOGS_ROOT:-logs}"

experiment_id="smoke_$(date +%Y%m%d_%H%M%S)"
runs_dir="${RESULTS_ROOT}/${experiment_id}"
judgments_out="${runs_dir}/judgments/${JUDGE_ID}.jsonl"
skips_out="${runs_dir}/judgments/${JUDGE_ID}.skips.jsonl"
aggregates_out="${runs_dir}/aggregates/summary.json"

mkdir -p "${LOGS_ROOT}"

echo "==> [1/3] Generating canonical runs (execution only)"
python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow "${FLOW_NAME}" \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --output-dir "${RESULTS_ROOT}" \
  --experiment-id "${experiment_id}" \
  --run-count "${RUN_COUNT}"

echo "==> [2/3] Scoring canonical runs"
python evals/score_runs.py \
  --config config/config.yaml \
  --runs-dir "${runs_dir}" \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --judge-model "${JUDGE_MODEL}" \
  --judge-id "${JUDGE_ID}" \
  --judge-prompt-version "${JUDGE_PROMPT_VERSION}" \
  --fail-on-skip \
  --skips-output "${skips_out}" \
  --output "${judgments_out}"

echo "==> [3/3] Summarizing runs + judgments"
python evals/summarize_results.py \
  --runs-dir "${runs_dir}" \
  --judgments-dir "${runs_dir}/judgments" \
  --output "${aggregates_out}"

echo
echo "Smoke run complete. Review outputs:"
echo "  Experiment ID: ${experiment_id}"
echo "  Canonical runs root: ${runs_dir}"
echo "  Judgments JSONL: ${judgments_out}"
echo "  Skips JSONL: ${skips_out}"
echo "  Aggregates summary: ${aggregates_out}"

echo
echo "Quick counts:"
if [[ -f "${judgments_out}" ]]; then
  echo "  Judgments total: $(wc -l < "${judgments_out}")"
else
  echo "  Judgments total: 0 (no judgments file found)"
fi
