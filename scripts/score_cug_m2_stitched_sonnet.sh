#!/usr/bin/env bash

set -euo pipefail

# CUG M2 scorer + summarizer for stitched Sonnet runs using a runs manifest.
#
# This is an alternate to scripts/score_cug_m2.sh when you want to score a
# curated set of run.json paths (e.g., "prefer new if exists, else old").
#
# Usage examples:
#   EXPERIMENT_ID=cug_m2_20260308_230032 scripts/score_cug_m2_stitched_sonnet.sh
#   RUNS_MANIFEST=results/cug_m2_20260308_230032/manifests/sonnet_prefer_new_if_exists.manifest.txt \
#     scripts/score_cug_m2_stitched_sonnet.sh

SCORING_CONFIG_PATH="${SCORING_CONFIG_PATH:-config/paper/cug_m1.yaml}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
RUNS_DIR="${RUNS_DIR:-}"
EXPERIMENT_ID="${EXPERIMENT_ID:-cug_m2_20260308_230032}"

JUDGE_MODEL="${JUDGE_MODEL:-gptoss}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
JUDGE_ID="${JUDGE_ID:-${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}_sonnet_prefer_new_if_exists}"
PASSING_SCORE="${PASSING_SCORE:-80}"

# 0 by default for exploratory runs so summary still writes; set to 1 for freeze.
FAIL_ON_SKIP="${FAIL_ON_SKIP:-0}"

TICKET_CASES_DEFAULT="${SCRATCH:-/tmp}/athos/data/ticket_cases"
CASES_DIRS="${CASES_DIRS:-${TICKET_CASES_DEFAULT}}"
QA_FILES="${QA_FILES:-evals/nersc_qa.v2.jsonl}"
STRICT_DATASET_PATHS="${STRICT_DATASET_PATHS:-0}"

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

RUNS_MANIFEST="${RUNS_MANIFEST:-${RUNS_DIR}/manifests/sonnet_prefer_new_if_exists.manifest.txt}"
if [[ ! -f "${RUNS_MANIFEST}" ]]; then
  echo "ERROR: runs manifest not found: ${RUNS_MANIFEST}" >&2
  exit 2
fi

read -r -a cases_args <<< "${CASES_DIRS}"
resolved_cases=()
missing_cases=()
for cases_dir in "${cases_args[@]}"; do
  [[ -z "${cases_dir}" ]] && continue
  if [[ -d "${cases_dir}" ]]; then
    resolved_cases+=("${cases_dir}")
  else
    missing_cases+=("${cases_dir}")
  fi
done

read -r -a qa_args <<< "${QA_FILES}"
resolved_qa=()
missing_qa=()
for qa_file in "${qa_args[@]}"; do
  [[ -z "${qa_file}" ]] && continue
  if [[ -f "${qa_file}" ]]; then
    resolved_qa+=("${qa_file}")
  else
    missing_qa+=("${qa_file}")
  fi
done

if [[ ${#resolved_cases[@]} -eq 0 && ${#resolved_qa[@]} -eq 0 ]]; then
  echo "ERROR: no valid reference datasets found from CASES_DIRS/QA_FILES." >&2
  exit 2
fi

if [[ "${STRICT_DATASET_PATHS}" == "1" && ( ${#missing_cases[@]} -gt 0 || ${#missing_qa[@]} -gt 0 ) ]]; then
  echo "ERROR: missing dataset paths under STRICT_DATASET_PATHS=1" >&2
  for item in "${missing_cases[@]}"; do
    echo "  missing cases-dir: ${item}" >&2
  done
  for item in "${missing_qa[@]}"; do
    echo "  missing qa-file: ${item}" >&2
  done
  exit 2
fi

JUDGMENTS_DIR="${JUDGMENTS_DIR:-${RUNS_DIR}/judgments}"
AGGREGATES_DIR="${AGGREGATES_DIR:-${RUNS_DIR}/aggregates}"
JUDGMENTS_OUT="${JUDGMENTS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.jsonl}"
SKIPS_OUT="${SKIPS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.skips.jsonl}"
SUMMARY_OUT="${SUMMARY_OUT:-${AGGREGATES_DIR}/summary_${JUDGE_ID}.json}"

mkdir -p "${JUDGMENTS_DIR}" "${AGGREGATES_DIR}"

score_cmd=(
  python evals/score_runs.py
  --config "${SCORING_CONFIG_PATH}"
  --runs-manifest "${RUNS_MANIFEST}"
  --judge-model "${JUDGE_MODEL}"
  --judge-id "${JUDGE_ID}"
  --judge-prompt-version "${JUDGE_PROMPT_VERSION}"
  --passing-score "${PASSING_SCORE}"
  --skips-output "${SKIPS_OUT}"
  --output "${JUDGMENTS_OUT}"
)

for cases_dir in "${resolved_cases[@]}"; do
  score_cmd+=(--cases-dir "${cases_dir}")
done

for qa_file in "${resolved_qa[@]}"; do
  score_cmd+=(--qa-file "${qa_file}")
done

if [[ "${FAIL_ON_SKIP}" == "1" ]]; then
  score_cmd+=(--fail-on-skip)
fi

echo "Scoring stitched CUG M2 Sonnet runs"
echo "  runs_dir: ${RUNS_DIR}"
echo "  runs_manifest: ${RUNS_MANIFEST}"
echo "  config: ${SCORING_CONFIG_PATH}"
echo "  judge_model: ${JUDGE_MODEL}"
echo "  judge_id: ${JUDGE_ID}"
echo "  fail_on_skip: ${FAIL_ON_SKIP}"
echo "  strict_dataset_paths: ${STRICT_DATASET_PATHS}"
echo "  judgments_out: ${JUDGMENTS_OUT}"
echo "  skips_out: ${SKIPS_OUT}"
echo "  started_at_utc: ${start_utc}"

if [[ ${#resolved_cases[@]} -gt 0 ]]; then
  echo "  cases_dirs: ${resolved_cases[*]}"
fi
if [[ ${#resolved_qa[@]} -gt 0 ]]; then
  echo "  qa_files: ${resolved_qa[*]}"
fi
if [[ ${#missing_cases[@]} -gt 0 ]]; then
  echo "  warning_missing_cases_dirs: ${missing_cases[*]}"
fi
if [[ ${#missing_qa[@]} -gt 0 ]]; then
  echo "  warning_missing_qa_files: ${missing_qa[*]}"
fi

"${score_cmd[@]}"

echo "Summarizing runs + stitched judgments"
echo "  summary_out: ${SUMMARY_OUT}"

python evals/summarize_results.py \
  --runs-dir "${RUNS_DIR}" \
  --judgment-file "${JUDGMENTS_OUT}" \
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
