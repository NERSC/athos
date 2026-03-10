#!/usr/bin/env bash

set -euo pipefail

# CUG M2 canonical run generator for ATHOS-native experiments.
#
# Defaults target expanded datasets while remaining compatible with existing M1 configs.
# Override any variable at invocation time as needed.
#
# Usage examples:
#   scripts/run_cug_m2.sh
#   FLOW_SET=base scripts/run_cug_m2.sh
#   FLOWS="cug_lang_base_gptoss cug_lang_chroma_gptoss" scripts/run_cug_m2.sh

CONFIG_PATH="${CONFIG_PATH:-config/paper/cug_m1.yaml}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
EXPERIMENT_ID="${EXPERIMENT_ID:-cug_m2_$(date +%Y%m%d_%H%M%S)}"
AGENT_SYSTEM="${AGENT_SYSTEM:-athos}"
RUN_COUNT="${RUN_COUNT:-1}"
RUN_START="${RUN_START:-0}"
ALLOW_OVERWRITE_RUNS="${ALLOW_OVERWRITE_RUNS:-0}"
AGGREGATE_MANIFEST="${AGGREGATE_MANIFEST:-$SCRATCH/athos/data/chroma/aggregates/manifests/athos_eval_bundle_20260306_local.json}"

# all | base | chroma
FLOW_SET="${FLOW_SET:-all}"
# Optional explicit override (space-separated flow names).
FLOWS="${FLOWS:-}"

# Expanded default dataset pointers for M2.
TICKET_CASES_DEFAULT="${SCRATCH}/athos/data/ticket_cases"
CASES_DIRS="${CASES_DIRS:-${TICKET_CASES_DEFAULT}}"
QA_FILES="${QA_FILES:-evals/nersc_qa.v2.jsonl}"

# 0 = warn/skip missing dataset paths, 1 = fail fast.
STRICT_DATASET_PATHS="${STRICT_DATASET_PATHS:-0}"
REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA="${REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA:-0}"

start_epoch="$(date +%s)"
start_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ -n "${FLOWS}" ]]; then
  read -r -a flow_args <<< "${FLOWS}"
else
  case "${FLOW_SET}" in
    all)
      flow_args=(
        cug_lang_base_gptoss
        cug_lang_base_sonnet
        cug_lang_chroma_gptoss
        #cug_lang_chroma_sonnet
      )
      ;;
    base)
      flow_args=(
        cug_lang_base_gptoss
        cug_lang_base_sonnet
      )
      ;;
    chroma)
      flow_args=(
        cug_lang_chroma_gptoss
        #cug_lang_chroma_sonnet
      )
      ;;
    *)
      echo "ERROR: FLOW_SET must be one of: all, base, chroma" >&2
      exit 2
      ;;
  esac
fi

if [[ ${#flow_args[@]} -eq 0 ]]; then
  echo "ERROR: no flows selected (set FLOW_SET or FLOWS)" >&2
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
    echo "ERROR: AGGREGATE_MANIFEST is required for chroma flows (set REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA=0 to bypass)." >&2
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
  echo "ERROR: no valid datasets found from CASES_DIRS/QA_FILES." >&2
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

cmd=(
  python evals/run_evaluations.py
  --config "${CONFIG_PATH}"
  --flow "${flow_args[@]}"
  --output-dir "${RESULTS_ROOT}"
  --experiment-id "${EXPERIMENT_ID}"
  --agent-system "${AGENT_SYSTEM}"
  --run-count "${RUN_COUNT}"
  --run-start "${RUN_START}"
)

for cases_dir in "${resolved_cases[@]}"; do
  cmd+=(--cases-dir "${cases_dir}")
done

for qa_file in "${resolved_qa[@]}"; do
  cmd+=(--qa-file "${qa_file}")
done

if [[ "${ALLOW_OVERWRITE_RUNS}" == "1" ]]; then
  cmd+=(--allow-overwrite-runs)
fi

if [[ -n "${AGGREGATE_MANIFEST}" ]]; then
  cmd+=(--aggregate-manifest "${AGGREGATE_MANIFEST}")
fi

echo "Running CUG M2 ATHOS experiments"
echo "  config: ${CONFIG_PATH}"
echo "  flows: ${flow_args[*]}"
echo "  experiment_id: ${EXPERIMENT_ID}"
echo "  output_root: ${RESULTS_ROOT}"
echo "  run_count/run_start: ${RUN_COUNT}/${RUN_START}"
echo "  started_at_utc: ${start_utc}"
echo "  strict_dataset_paths: ${STRICT_DATASET_PATHS}"

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
if [[ -n "${AGGREGATE_MANIFEST}" ]]; then
  echo "  aggregate_manifest: ${AGGREGATE_MANIFEST}"
fi

"${cmd[@]}"

end_epoch="$(date +%s)"
end_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
elapsed_sec="$((end_epoch - start_epoch))"

echo "Done. Canonical runs written to:"
echo "  ${RESULTS_ROOT}/${EXPERIMENT_ID}"
echo "Run timing summary:"
echo "  started_at_utc: ${start_utc}"
echo "  finished_at_utc: ${end_utc}"
echo "  elapsed_seconds: ${elapsed_sec}"
