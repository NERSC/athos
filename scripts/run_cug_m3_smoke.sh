#!/usr/bin/env bash

set -euo pipefail

# CUG M3 smoke runner (simple_qa-only) with built-in scoring + summary.
#
# Purpose:
# - Fast functional validation of selected M3 flows on small QA-only dataset.
# - Avoid ticket-case execution during smoke by design.
#
# Usage examples:
#   scripts/run_cug_m3_smoke.sh
#   FLOWS="cug_lang_chroma_gptoss_opt cug_smol_chroma_gptoss" scripts/run_cug_m3_smoke.sh
#   RUN_COUNT=2 QA_FILES="evals/simple_qa.jsonl" scripts/run_cug_m3_smoke.sh

CONFIG_PATH="${CONFIG_PATH:-config/paper/cug_m1.yaml}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
EXPERIMENT_ID="${EXPERIMENT_ID:-cug_m3_smoke_$(date +%Y%m%d_%H%M%S)}"
RUNS_DIR="${RUNS_DIR:-${RESULTS_ROOT}/${EXPERIMENT_ID}}"
AGENT_SYSTEM="${AGENT_SYSTEM:-athos}"
RUN_COUNT="${RUN_COUNT:-1}"
RUN_START="${RUN_START:-0}"
ALLOW_OVERWRITE_RUNS="${ALLOW_OVERWRITE_RUNS:-0}"

# QA-only smoke defaults.
QA_FILES="${QA_FILES:-evals/simple_qa.jsonl}"
STRICT_QA_PATHS="${STRICT_QA_PATHS:-1}"

# Default flow set for M3 smoke.
FLOWS="${FLOWS:-cug_lang_chroma_gptoss_opt cug_smol_chroma_gptoss cug_lang_filesystem_gptoss}"

AGGREGATE_MANIFEST="${AGGREGATE_MANIFEST:-$SCRATCH/athos/data/chroma/aggregates/manifests/athos_eval_bundle_20260306_local.json}"
REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA="${REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA:-1}"

# Scoring defaults.
JUDGE_MODEL="${JUDGE_MODEL:-gptoss}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
JUDGE_ID="${JUDGE_ID:-${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}}"
PASSING_SCORE="${PASSING_SCORE:-80}"
FAIL_ON_SKIP="${FAIL_ON_SKIP:-0}"
SCORING_CONFIG_PATH="${SCORING_CONFIG_PATH:-${CONFIG_PATH}}"

JUDGMENTS_DIR="${JUDGMENTS_DIR:-${RUNS_DIR}/judgments}"
AGGREGATES_DIR="${AGGREGATES_DIR:-${RUNS_DIR}/aggregates}"
JUDGMENTS_OUT="${JUDGMENTS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.jsonl}"
SKIPS_OUT="${SKIPS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.skips.jsonl}"
SUMMARY_OUT="${SUMMARY_OUT:-${AGGREGATES_DIR}/summary.json}"

start_epoch="$(date +%s)"
start_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

read -r -a flow_args <<< "${FLOWS}"
if [[ ${#flow_args[@]} -eq 0 ]]; then
  echo "ERROR: no flows selected (set FLOWS)" >&2
  exit 2
fi

has_chroma_flow=0
for flow in "${flow_args[@]}"; do
  if [[ "${flow}" == *"chroma"* ]]; then
    has_chroma_flow=1
    break
  fi
done

if [[ "${has_chroma_flow}" == "1" ]]; then
  if [[ "${REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA}" == "1" && -z "${AGGREGATE_MANIFEST}" ]]; then
    echo "ERROR: AGGREGATE_MANIFEST is required for chroma flows." >&2
    exit 2
  fi
fi

if [[ -n "${AGGREGATE_MANIFEST}" && ! -f "${AGGREGATE_MANIFEST}" ]]; then
  if [[ "${REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA}" == "1" && "${has_chroma_flow}" == "1" ]]; then
    echo "ERROR: aggregate manifest not found: ${AGGREGATE_MANIFEST}" >&2
    exit 2
  fi
  echo "WARN: aggregate manifest not found, proceeding without aggregate provenance: ${AGGREGATE_MANIFEST}" >&2
  AGGREGATE_MANIFEST=""
fi

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

if [[ ${#resolved_qa[@]} -eq 0 ]]; then
  echo "ERROR: no valid QA datasets found from QA_FILES." >&2
  exit 2
fi

if [[ "${STRICT_QA_PATHS}" == "1" && ${#missing_qa[@]} -gt 0 ]]; then
  echo "ERROR: missing qa-file paths under STRICT_QA_PATHS=1" >&2
  for item in "${missing_qa[@]}"; do
    echo "  missing qa-file: ${item}" >&2
  done
  exit 2
fi

run_cmd=(
  python evals/run_evaluations.py
  --config "${CONFIG_PATH}"
  --flow "${flow_args[@]}"
  --output-dir "${RESULTS_ROOT}"
  --experiment-id "${EXPERIMENT_ID}"
  --agent-system "${AGENT_SYSTEM}"
  --run-count "${RUN_COUNT}"
  --run-start "${RUN_START}"
)

for qa_file in "${resolved_qa[@]}"; do
  run_cmd+=(--qa-file "${qa_file}")
done

if [[ "${ALLOW_OVERWRITE_RUNS}" == "1" ]]; then
  run_cmd+=(--allow-overwrite-runs)
fi

if [[ -n "${AGGREGATE_MANIFEST}" ]]; then
  run_cmd+=(--aggregate-manifest "${AGGREGATE_MANIFEST}")
fi

echo "Running CUG M3 smoke (QA-only)"
echo "  config: ${CONFIG_PATH}"
echo "  flows: ${flow_args[*]}"
echo "  experiment_id: ${EXPERIMENT_ID}"
echo "  output_root: ${RESULTS_ROOT}"
echo "  run_count/run_start: ${RUN_COUNT}/${RUN_START}"
echo "  started_at_utc: ${start_utc}"
echo "  qa_files: ${resolved_qa[*]}"
if [[ ${#missing_qa[@]} -gt 0 ]]; then
  echo "  warning_missing_qa_files: ${missing_qa[*]}"
fi
if [[ -n "${AGGREGATE_MANIFEST}" ]]; then
  echo "  aggregate_manifest: ${AGGREGATE_MANIFEST}"
fi

"${run_cmd[@]}"

if [[ ! -d "${RUNS_DIR}" ]]; then
  echo "ERROR: runs directory not found after execution: ${RUNS_DIR}" >&2
  exit 2
fi

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

for qa_file in "${resolved_qa[@]}"; do
  score_cmd+=(--qa-file "${qa_file}")
done

if [[ "${FAIL_ON_SKIP}" == "1" ]]; then
  score_cmd+=(--fail-on-skip)
fi

echo "Scoring CUG M3 smoke runs"
echo "  runs_dir: ${RUNS_DIR}"
echo "  judge_id: ${JUDGE_ID}"
echo "  fail_on_skip: ${FAIL_ON_SKIP}"
echo "  judgments_out: ${JUDGMENTS_OUT}"
echo "  skips_out: ${SKIPS_OUT}"

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
echo "  Runs: ${RUNS_DIR}"
echo "  Judgments: ${JUDGMENTS_OUT}"
echo "  Skips: ${SKIPS_OUT}"
echo "  Summary: ${SUMMARY_OUT}"
echo "Run timing summary:"
echo "  started_at_utc: ${start_utc}"
echo "  finished_at_utc: ${end_utc}"
echo "  elapsed_seconds: ${elapsed_sec}"
