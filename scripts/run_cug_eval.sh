#!/usr/bin/env bash

set -euo pipefail

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

usage() {
  cat <<'EOF'
Usage:
  scripts/run_cug_eval.sh --dataset-profile <profile> --flow-profile <profile> [options]

Dataset profiles:
  mini_tickets  -> evals/test_cases
  mini_qa       -> evals/simple_qa.jsonl
  mini          -> evals/test_cases + evals/simple_qa.jsonl
  full_tickets  -> data/ticket_cases
  full_qa       -> evals/nersc_qa.v2.jsonl
  full          -> data/ticket_cases + evals/nersc_qa.v2.jsonl

Flow profiles:
  lang_base_gptoss         -> cug_lang_base_gptoss
  lang_base_sonnet         -> cug_lang_base_sonnet
  lang_chroma_gptoss       -> cug_lang_chroma_gptoss
  lang_chroma_sonnet       -> cug_lang_chroma_sonnet
  lang_chroma_gptoss_opt   -> cug_lang_chroma_gptoss_opt
  lang_chroma_sonnet_opt   -> cug_lang_chroma_sonnet_opt
  smol_chroma_gptoss       -> cug_smol_chroma_gptoss
  smol_chroma_sonnet       -> cug_smol_chroma_sonnet
  lang_filesystem_gptoss   -> cug_lang_filesystem_gptoss
  lang_filesystem_sonnet   -> cug_lang_filesystem_sonnet

Options:
  --dataset-profile <profile>     Dataset preset to use.
  --flow-profile <profile>        Flow preset to use.
  --run-count <n>                 Number of runs per case/question. Default: 1
  --run-start <n>                 Starting run index. Default: 0
  --experiment-id <id>            Override experiment id.
  --results-root <dir>            Results root. Default: results
  --config <path>                 Config path. Default: config/paper/cug_m1.yaml
  --aggregate-manifest <path>     Aggregate manifest for provenance.
  --judge-model <name>            Judge model. Default: gptoss
  --judge-prompt-version <name>   Judge prompt version. Default: rubric_v1
  --passing-score <n>             Passing score threshold. Default: 80
  --strict-dataset-paths <0|1>    Require dataset paths to exist. Default: 1
  --skip-execution                Skip eval execution and only run score+summarize.
  --skip-scoring                  Skip score+summarize and only run execution.
  --debug-shell                   Enable shell tracing and stage debug logs.
  --allow-overwrite-runs          Pass --allow-overwrite-runs through.
  --fail-on-skip                  Fail scoring when skips are present.
  --list-profiles                 Print dataset/flow profiles and exit.
  -h, --help                      Show this help text.

Examples:
  scripts/run_cug_eval.sh \
    --dataset-profile mini \
    --flow-profile lang_chroma_gptoss_opt

  scripts/run_cug_eval.sh \
    --dataset-profile full_tickets \
    --flow-profile lang_filesystem_gptoss \
    --run-count 1
EOF
}

list_profiles() {
  usage | awk '
    /^Dataset profiles:/ {printing=1}
    /^Options:/ {printing=0}
    printing {print}
  '
}

resolve_dataset_profile() {
  local profile="$1"
  CASES_DIRS=""
  QA_FILES=""
  case "${profile}" in
    mini_tickets)
      CASES_DIRS="evals/test_cases"
      ;;
    mini_qa)
      QA_FILES="evals/simple_qa.jsonl"
      ;;
    mini)
      CASES_DIRS="evals/test_cases"
      QA_FILES="evals/simple_qa.jsonl"
      ;;
    full_tickets)
      CASES_DIRS="data/ticket_cases"
      ;;
    full_qa)
      QA_FILES="evals/nersc_qa.v2.jsonl"
      ;;
    full)
      CASES_DIRS="data/ticket_cases"
      QA_FILES="evals/nersc_qa.v2.jsonl"
      ;;
    *)
      echo "ERROR: unknown dataset profile: ${profile}" >&2
      exit 2
      ;;
  esac
}

resolve_flow_profile() {
  local profile="$1"
  case "${profile}" in
    lang_base_gptoss) FLOW_NAME="cug_lang_base_gptoss" ;;
    lang_base_sonnet) FLOW_NAME="cug_lang_base_sonnet" ;;
    lang_chroma_gptoss) FLOW_NAME="cug_lang_chroma_gptoss" ;;
    lang_chroma_sonnet) FLOW_NAME="cug_lang_chroma_sonnet" ;;
    lang_chroma_gptoss_opt) FLOW_NAME="cug_lang_chroma_gptoss_opt" ;;
    lang_chroma_sonnet_opt) FLOW_NAME="cug_lang_chroma_sonnet_opt" ;;
    smol_chroma_gptoss) FLOW_NAME="cug_smol_chroma_gptoss" ;;
    smol_chroma_sonnet) FLOW_NAME="cug_smol_chroma_sonnet" ;;
    lang_filesystem_gptoss) FLOW_NAME="cug_lang_filesystem_gptoss" ;;
    lang_filesystem_sonnet) FLOW_NAME="cug_lang_filesystem_sonnet" ;;
    *)
      echo "ERROR: unknown flow profile: ${profile}" >&2
      exit 2
      ;;
  esac
}

CONFIG_PATH="${CONFIG_PATH:-config/paper/cug_m1.yaml}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
AGENT_SYSTEM="${AGENT_SYSTEM:-athos}"
RUN_COUNT="${RUN_COUNT:-1}"
RUN_START="${RUN_START:-0}"
ALLOW_OVERWRITE_RUNS="${ALLOW_OVERWRITE_RUNS:-0}"
STRICT_DATASET_PATHS="${STRICT_DATASET_PATHS:-1}"
SKIP_EXECUTION="${SKIP_EXECUTION:-0}"
SKIP_SCORING="${SKIP_SCORING:-0}"
DEBUG_SHELL="${DEBUG_SHELL:-0}"
JUDGE_MODEL="${JUDGE_MODEL:-gptoss}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
JUDGE_MAX_ATTEMPTS="${JUDGE_MAX_ATTEMPTS:-5}"
JUDGE_RETRY_DELAY_MS="${JUDGE_RETRY_DELAY_MS:-1500}"
PASSING_SCORE="${PASSING_SCORE:-80}"
FAIL_ON_SKIP="${FAIL_ON_SKIP:-0}"
SCORING_CONFIG_PATH="${SCORING_CONFIG_PATH:-${CONFIG_PATH}}"
AGGREGATE_MANIFEST="${AGGREGATE_MANIFEST:-data/chroma/aggregates/manifests/athos_eval_bundle_20260318_derived_tickets_lt_20250901_v2.json}"

DATASET_PROFILE=""
FLOW_PROFILE=""
EXPERIMENT_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dataset-profile)
      DATASET_PROFILE="$2"
      shift 2
      ;;
    --flow-profile)
      FLOW_PROFILE="$2"
      shift 2
      ;;
    --run-count)
      RUN_COUNT="$2"
      shift 2
      ;;
    --run-start)
      RUN_START="$2"
      shift 2
      ;;
    --experiment-id)
      EXPERIMENT_ID="$2"
      shift 2
      ;;
    --results-root)
      RESULTS_ROOT="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      SCORING_CONFIG_PATH="$2"
      shift 2
      ;;
    --aggregate-manifest)
      AGGREGATE_MANIFEST="$2"
      shift 2
      ;;
    --judge-model)
      JUDGE_MODEL="$2"
      shift 2
      ;;
    --judge-prompt-version)
      JUDGE_PROMPT_VERSION="$2"
      shift 2
      ;;
    --passing-score)
      PASSING_SCORE="$2"
      shift 2
      ;;
    --strict-dataset-paths)
      STRICT_DATASET_PATHS="$2"
      shift 2
      ;;
    --skip-execution)
      SKIP_EXECUTION=1
      shift
      ;;
    --skip-scoring)
      SKIP_SCORING=1
      shift
      ;;
    --debug-shell)
      DEBUG_SHELL=1
      shift
      ;;
    --allow-overwrite-runs)
      ALLOW_OVERWRITE_RUNS=1
      shift
      ;;
    --fail-on-skip)
      FAIL_ON_SKIP=1
      shift
      ;;
    --list-profiles)
      list_profiles
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${DATASET_PROFILE}" || -z "${FLOW_PROFILE}" ]]; then
  echo "ERROR: --dataset-profile and --flow-profile are required." >&2
  usage >&2
  exit 2
fi

resolve_dataset_profile "${DATASET_PROFILE}"
resolve_flow_profile "${FLOW_PROFILE}"

if [[ "${DEBUG_SHELL}" == "1" ]]; then
  set -x
fi

if [[ -z "${EXPERIMENT_ID}" ]]; then
  EXPERIMENT_ID="cug_${DATASET_PROFILE}_${FLOW_PROFILE}_$(date +%Y%m%d_%H%M%S)"
fi

RUNS_DIR="${RESULTS_ROOT}/${EXPERIMENT_ID}"
JUDGE_ID="${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}"
JUDGMENTS_DIR="${RUNS_DIR}/judgments"
AGGREGATES_DIR="${RUNS_DIR}/aggregates"
JUDGMENTS_OUT="${JUDGMENTS_DIR}/${JUDGE_ID}.jsonl"
SKIPS_OUT="${JUDGMENTS_DIR}/${JUDGE_ID}.skips.jsonl"
SUMMARY_OUT="${AGGREGATES_DIR}/summary.json"
RUN_LOG="${RUNS_DIR}/run_evaluations.log"
SCORE_LOG="${RUNS_DIR}/score_runs.log"
SUMMARY_LOG="${RUNS_DIR}/summarize_results.log"

start_epoch="$(date +%s)"
start_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ "${FLOW_NAME}" == *"chroma"* && -n "${AGGREGATE_MANIFEST}" && ! -f "${AGGREGATE_MANIFEST}" ]]; then
  echo "ERROR: aggregate manifest not found: ${AGGREGATE_MANIFEST}" >&2
  exit 2
fi

cases_args=()
if [[ -n "${CASES_DIRS}" ]]; then
  read -r -a cases_args <<< "${CASES_DIRS}"
fi
resolved_cases=()
missing_cases=()
if [[ ${#cases_args[@]} -gt 0 ]]; then
  for cases_dir in "${cases_args[@]}"; do
    [[ -z "${cases_dir}" ]] && continue
    if [[ -d "${cases_dir}" ]]; then
      resolved_cases+=("${cases_dir}")
    else
      missing_cases+=("${cases_dir}")
    fi
  done
fi

qa_args=()
if [[ -n "${QA_FILES}" ]]; then
  read -r -a qa_args <<< "${QA_FILES}"
fi
resolved_qa=()
missing_qa=()
if [[ ${#qa_args[@]} -gt 0 ]]; then
  for qa_file in "${qa_args[@]}"; do
    [[ -z "${qa_file}" ]] && continue
    if [[ -f "${qa_file}" ]]; then
      resolved_qa+=("${qa_file}")
    else
      missing_qa+=("${qa_file}")
    fi
  done
fi

if [[ ${#resolved_cases[@]} -eq 0 && ${#resolved_qa[@]} -eq 0 ]]; then
  echo "ERROR: no valid datasets found from dataset profile ${DATASET_PROFILE}." >&2
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

quote_cmd() {
  local rendered=""
  local arg
  for arg in "$@"; do
    rendered+=" $(printf '%q' "${arg}")"
  done
  rendered="${rendered# }"
  printf '%s\n' "${rendered}"
}

log_stage_header() {
  local stage="$1"
  local logfile="$2"
  echo "[${stage}] started_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[${stage}] log=${logfile}"
}

validate_nonempty_jsonl() {
  local path="$1"
  local label="$2"
  if [[ ! -f "${path}" ]]; then
    echo "ERROR: ${label} file missing: ${path}" >&2
    return 1
  fi
  local line_count
  line_count="$(wc -l < "${path}")"
  echo "  ${label}_lines: ${line_count}"
  if [[ "${line_count}" -eq 0 ]]; then
    echo "ERROR: ${label} file is empty: ${path}" >&2
    return 1
  fi
}

run_cmd=(
  python evals/run_evaluations.py
  --config "${CONFIG_PATH}"
  --flow "${FLOW_NAME}"
  --output-dir "${RESULTS_ROOT}"
  --experiment-id "${EXPERIMENT_ID}"
  --agent-system "${AGENT_SYSTEM}"
  --run-count "${RUN_COUNT}"
  --run-start "${RUN_START}"
)

if [[ ${#resolved_cases[@]} -gt 0 ]]; then
  for cases_dir in "${resolved_cases[@]}"; do
    run_cmd+=(--cases-dir "${cases_dir}")
  done
fi
if [[ ${#resolved_qa[@]} -gt 0 ]]; then
  for qa_file in "${resolved_qa[@]}"; do
    run_cmd+=(--qa-file "${qa_file}")
  done
fi
if [[ "${ALLOW_OVERWRITE_RUNS}" == "1" ]]; then
  run_cmd+=(--allow-overwrite-runs)
fi
if [[ "${FLOW_NAME}" == *"chroma"* && -n "${AGGREGATE_MANIFEST}" ]]; then
  run_cmd+=(--aggregate-manifest "${AGGREGATE_MANIFEST}")
fi

echo "Running CUG eval"
echo "  config: ${CONFIG_PATH}"
echo "  dataset_profile: ${DATASET_PROFILE}"
echo "  flow_profile: ${FLOW_PROFILE}"
echo "  flow_name: ${FLOW_NAME}"
echo "  experiment_id: ${EXPERIMENT_ID}"
echo "  output_root: ${RESULTS_ROOT}"
echo "  run_count/run_start: ${RUN_COUNT}/${RUN_START}"
echo "  skip_execution: ${SKIP_EXECUTION}"
echo "  skip_scoring: ${SKIP_SCORING}"
echo "  debug_shell: ${DEBUG_SHELL}"
echo "  started_at_utc: ${start_utc}"
if [[ ${#resolved_cases[@]} -gt 0 ]]; then
  echo "  cases_dirs: ${resolved_cases[*]}"
fi
if [[ ${#resolved_qa[@]} -gt 0 ]]; then
  echo "  qa_files: ${resolved_qa[*]}"
fi
if [[ "${FLOW_NAME}" == *"chroma"* && -n "${AGGREGATE_MANIFEST}" ]]; then
  echo "  aggregate_manifest: ${AGGREGATE_MANIFEST}"
fi

mkdir -p "${RUNS_DIR}"

if [[ "${SKIP_EXECUTION}" != "1" ]]; then
  log_stage_header "run_evaluations" "${RUN_LOG}"
  echo "  command: $(quote_cmd "${run_cmd[@]}")"
  {
    echo "COMMAND $(quote_cmd "${run_cmd[@]}")"
    "${run_cmd[@]}"
  } 2>&1 | tee "${RUN_LOG}"
else
  echo "Skipping execution stage because --skip-execution was set."
fi

if [[ ! -d "${RUNS_DIR}" ]]; then
  echo "ERROR: runs directory not found after execution: ${RUNS_DIR}" >&2
  exit 2
fi

if [[ "${SKIP_SCORING}" == "1" ]]; then
  echo "Skipping score+summarize stage because --skip-scoring was set."
  exit 0
fi

mkdir -p "${JUDGMENTS_DIR}" "${AGGREGATES_DIR}"

score_cmd=(
  python evals/score_runs.py
  --config "${SCORING_CONFIG_PATH}"
  --runs-dir "${RUNS_DIR}"
  --judge-model "${JUDGE_MODEL}"
  --judge-id "${JUDGE_ID}"
  --judge-prompt-version "${JUDGE_PROMPT_VERSION}"
  --judge-max-attempts "${JUDGE_MAX_ATTEMPTS}"
  --judge-retry-delay-ms "${JUDGE_RETRY_DELAY_MS}"
  --passing-score "${PASSING_SCORE}"
  --skips-output "${SKIPS_OUT}"
  --output "${JUDGMENTS_OUT}"
)

if [[ ${#resolved_cases[@]} -gt 0 ]]; then
  for cases_dir in "${resolved_cases[@]}"; do
    score_cmd+=(--cases-dir "${cases_dir}")
  done
fi
if [[ ${#resolved_qa[@]} -gt 0 ]]; then
  for qa_file in "${resolved_qa[@]}"; do
    score_cmd+=(--qa-file "${qa_file}")
  done
fi
if [[ "${FAIL_ON_SKIP}" == "1" ]]; then
  score_cmd+=(--fail-on-skip)
fi

echo "Scoring CUG eval runs"
echo "  runs_dir: ${RUNS_DIR}"
echo "  judge_id: ${JUDGE_ID}"
echo "  judge_max_attempts: ${JUDGE_MAX_ATTEMPTS}"
echo "  judge_retry_delay_ms: ${JUDGE_RETRY_DELAY_MS}"
echo "  fail_on_skip: ${FAIL_ON_SKIP}"
echo "  judgments_out: ${JUDGMENTS_OUT}"
echo "  skips_out: ${SKIPS_OUT}"
log_stage_header "score_runs" "${SCORE_LOG}"
echo "  command: $(quote_cmd "${score_cmd[@]}")"

{
  echo "COMMAND $(quote_cmd "${score_cmd[@]}")"
  "${score_cmd[@]}"
} > "${SCORE_LOG}" 2>&1

tail -200 "${SCORE_LOG}" || true

echo "Scoring artifact check"
ls -l "${JUDGMENTS_OUT}" "${SKIPS_OUT}" 2>/dev/null || true
validate_nonempty_jsonl "${JUDGMENTS_OUT}" "judgments"
if [[ -f "${SKIPS_OUT}" ]]; then
  echo "  skips_lines: $(wc -l < "${SKIPS_OUT}")"
fi

echo "Summarizing runs + judgments"
echo "  summary_out: ${SUMMARY_OUT}"
log_stage_header "summarize_results" "${SUMMARY_LOG}"
echo "  command: $(quote_cmd python evals/summarize_results.py --runs-dir "${RUNS_DIR}" --judgments-dir "${JUDGMENTS_DIR}" --judge-id "${JUDGE_ID}" --output "${SUMMARY_OUT}")"

{
  echo "COMMAND $(quote_cmd python evals/summarize_results.py --runs-dir "${RUNS_DIR}" --judgments-dir "${JUDGMENTS_DIR}" --judge-id "${JUDGE_ID}" --output "${SUMMARY_OUT}")"
  python evals/summarize_results.py \
    --runs-dir "${RUNS_DIR}" \
    --judgments-dir "${JUDGMENTS_DIR}" \
    --judge-id "${JUDGE_ID}" \
    --output "${SUMMARY_OUT}"
} > "${SUMMARY_LOG}" 2>&1

tail -200 "${SUMMARY_LOG}" || true

if [[ ! -f "${SUMMARY_OUT}" ]]; then
  echo "ERROR: summary file missing: ${SUMMARY_OUT}" >&2
  exit 2
fi

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
