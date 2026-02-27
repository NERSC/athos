#!/usr/bin/env bash

set -euo pipefail

# CUG M1 canonical run generator for ATHOS-native experiments (E1-E4).
# External coding-agent baselines are run outside ATHOS and imported separately.
#
# Usage examples:
#   scripts/run_cug_m1.sh
#   FLOW_SET=base scripts/run_cug_m1.sh
#   FLOW_SET=chroma AGGREGATE_MANIFEST=/path/to/aggregate.json ATHOS_CHROMA_PERSIST_DIR=/path/to/chroma scripts/run_cug_m1.sh
#   FLOWS="cug_lang_base_gptoss cug_lang_chroma_gptoss" scripts/run_cug_m1.sh

CONFIG_PATH="${CONFIG_PATH:-config/paper/cug_m1.yaml}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
EXPERIMENT_ID="${EXPERIMENT_ID:-cug_m1_$(date +%Y%m%d_%H%M%S)}"
AGENT_SYSTEM="${AGENT_SYSTEM:-athos}"
RUN_COUNT="${RUN_COUNT:-1}"
RUN_START="${RUN_START:-0}"
ALLOW_OVERWRITE_RUNS="${ALLOW_OVERWRITE_RUNS:-0}"
AGGREGATE_MANIFEST="${AGGREGATE_MANIFEST:-}"

# all | base | chroma
FLOW_SET="${FLOW_SET:-all}"
# Optional explicit override (space-separated flow names).
FLOWS="${FLOWS:-}"

CASES_DIRS="${CASES_DIRS:-evals/test_cases}"
QA_FILES="${QA_FILES:-evals/simple_qa.jsonl}"
REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA="${REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA:-1}"

if [[ -n "${FLOWS}" ]]; then
  read -r -a flow_args <<< "${FLOWS}"
else
  case "${FLOW_SET}" in
    all)
      flow_args=(
        cug_lang_base_gptoss
        cug_smol_base_gptoss
        cug_lang_chroma_gptoss
        cug_smol_chroma_gptoss
      )
      ;;
    base)
      flow_args=(
        cug_lang_base_gptoss
        cug_smol_base_gptoss
      )
      ;;
    chroma)
      flow_args=(
        cug_lang_chroma_gptoss
        cug_smol_chroma_gptoss
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
  if [[ -z "${ATHOS_CHROMA_PERSIST_DIR:-}" ]]; then
    echo "ERROR: ATHOS_CHROMA_PERSIST_DIR must be set for chroma flows." >&2
    exit 2
  fi
  if [[ "${REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA}" == "1" && -z "${AGGREGATE_MANIFEST}" ]]; then
    echo "ERROR: AGGREGATE_MANIFEST is required for chroma flows (set REQUIRE_AGGREGATE_MANIFEST_FOR_CHROMA=0 to bypass)." >&2
    exit 2
  fi
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

read -r -a cases_args <<< "${CASES_DIRS}"
for cases_dir in "${cases_args[@]}"; do
  [[ -n "${cases_dir}" ]] && cmd+=(--cases-dir "${cases_dir}")
done

read -r -a qa_args <<< "${QA_FILES}"
for qa_file in "${qa_args[@]}"; do
  [[ -n "${qa_file}" ]] && cmd+=(--qa-file "${qa_file}")
done

if [[ "${ALLOW_OVERWRITE_RUNS}" == "1" ]]; then
  cmd+=(--allow-overwrite-runs)
fi

if [[ -n "${AGGREGATE_MANIFEST}" ]]; then
  cmd+=(--aggregate-manifest "${AGGREGATE_MANIFEST}")
fi

echo "Running CUG M1 ATHOS experiments"
echo "  config: ${CONFIG_PATH}"
echo "  flows: ${flow_args[*]}"
echo "  experiment_id: ${EXPERIMENT_ID}"
echo "  output_root: ${RESULTS_ROOT}"
echo "  run_count/run_start: ${RUN_COUNT}/${RUN_START}"
if [[ "${has_chroma_flow}" == "1" ]]; then
  echo "  chroma_persist_dir: ${ATHOS_CHROMA_PERSIST_DIR}"
fi
if [[ -n "${AGGREGATE_MANIFEST}" ]]; then
  echo "  aggregate_manifest: ${AGGREGATE_MANIFEST}"
fi

"${cmd[@]}"

echo "Done. Canonical runs written to:"
echo "  ${RESULTS_ROOT}/${EXPERIMENT_ID}"
