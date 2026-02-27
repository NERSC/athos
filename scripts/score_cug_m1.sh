#!/usr/bin/env bash

set -euo pipefail

# CUG M1 scorer + summarizer for canonical runs.
#
# Usage examples:
#   EXPERIMENT_ID=cug_m1_20260227_120000 scripts/score_cug_m1.sh
#   RUNS_DIR=results/cug_m1_20260227_120000 scripts/score_cug_m1.sh
#   EXPERIMENT_ID=cug_m1_20260227_120000 JUDGE_MODEL=gptoss scripts/score_cug_m1.sh

SCORING_CONFIG_PATH="${SCORING_CONFIG_PATH:-config/paper/cug_m1.yaml}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
RUNS_DIR="${RUNS_DIR:-}"
EXPERIMENT_ID="${EXPERIMENT_ID:-}"

JUDGE_MODEL="${JUDGE_MODEL:-gptoss}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
JUDGE_ID="${JUDGE_ID:-${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}}"
PASSING_SCORE="${PASSING_SCORE:-80}"
FAIL_ON_SKIP="${FAIL_ON_SKIP:-1}"

CASES_DIRS="${CASES_DIRS:-evals/test_cases}"
QA_FILES="${QA_FILES:-evals/simple_qa.jsonl}"

start_epoch="$(date +%s)"
start_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ -z "${RUNS_DIR}" ]]; then
  if [[ -z "${EXPERIMENT_ID}" ]]; then
    echo "ERROR: set RUNS_DIR or EXPERIMENT_ID" >&2
    exit 2
  fi
  RUNS_DIR="${RESULTS_ROOT}/${EXPERIMENT_ID}"
fi

if [[ ! -d "${RUNS_DIR}" ]]; then
  echo "ERROR: runs directory not found: ${RUNS_DIR}" >&2
  exit 2
fi

JUDGMENTS_DIR="${JUDGMENTS_DIR:-${RUNS_DIR}/judgments}"
AGGREGATES_DIR="${AGGREGATES_DIR:-${RUNS_DIR}/aggregates}"
JUDGMENTS_OUT="${JUDGMENTS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.jsonl}"
SKIPS_OUT="${SKIPS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.skips.jsonl}"
SUMMARY_OUT="${SUMMARY_OUT:-${AGGREGATES_DIR}/summary.json}"

mkdir -p "${JUDGMENTS_DIR}" "${AGGREGATES_DIR}"

score_cmd=(
  python evals/score_runs.py
  --config "${SCORING_CONFIG_PATH}"
  --runs-dir "${RUNS_DIR}"
  --judge-model "${JUDGE_MODEL}"
  --judge-id "${JUDGE_ID}"
  --judge-prompt-version "${JUDGE_PROMPT_VERSION}"
  --passing-score "${PASSING_SCORE}"
  --skips-output "${SKIPS_OUT}"
  --output "${JUDGMENTS_OUT}"
)

read -r -a cases_args <<< "${CASES_DIRS}"
for cases_dir in "${cases_args[@]}"; do
  [[ -n "${cases_dir}" ]] && score_cmd+=(--cases-dir "${cases_dir}")
done

read -r -a qa_args <<< "${QA_FILES}"
for qa_file in "${qa_args[@]}"; do
  [[ -n "${qa_file}" ]] && score_cmd+=(--qa-file "${qa_file}")
done

if [[ "${FAIL_ON_SKIP}" == "1" ]]; then
  score_cmd+=(--fail-on-skip)
fi

echo "Scoring CUG M1 runs"
echo "  runs_dir: ${RUNS_DIR}"
echo "  config: ${SCORING_CONFIG_PATH}"
echo "  judge_model: ${JUDGE_MODEL}"
echo "  judge_id: ${JUDGE_ID}"
echo "  fail_on_skip: ${FAIL_ON_SKIP}"
echo "  judgments_out: ${JUDGMENTS_OUT}"
echo "  skips_out: ${SKIPS_OUT}"
echo "  started_at_utc: ${start_utc}"

"${score_cmd[@]}"

echo "Summarizing runs + judgments"
echo "  summary_out: ${SUMMARY_OUT}"

python evals/summarize_results.py \
  --runs-dir "${RUNS_DIR}" \
  --judgments-dir "${JUDGMENTS_DIR}" \
  --output "${SUMMARY_OUT}"

end_epoch="$(date +%s)"
end_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
elapsed_sec="$((end_epoch - start_epoch))"

echo "Done."
echo "  Judgments: ${JUDGMENTS_OUT}"
echo "  Skips: ${SKIPS_OUT}"
echo "  Summary: ${SUMMARY_OUT}"
echo "Run timing summary:"
echo "  started_at_utc: ${start_utc}"
echo "  finished_at_utc: ${end_utc}"
echo "  elapsed_seconds: ${elapsed_sec}"
