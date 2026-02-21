#!/usr/bin/env bash

set -euo pipefail

# Canonical eval sweep runner (execution only).
# Override via environment variables as needed.
CONFIG_PATH="${CONFIG_PATH:-config/config.yaml}"
FLOWS="${FLOWS:-lang_docs_react_agent}"
CASES_DIRS="${CASES_DIRS:-evals/test_cases}"
QA_FILES="${QA_FILES:-evals/simple_qa.jsonl}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
EXPERIMENT_ID="${EXPERIMENT_ID:-sweep_$(date +%Y%m%d_%H%M%S)}"
AGENT_SYSTEM="${AGENT_SYSTEM:-athos}"
RUN_COUNT="${RUN_COUNT:-1}"
RUN_START="${RUN_START:-0}"
ALLOW_OVERWRITE_RUNS="${ALLOW_OVERWRITE_RUNS:-0}"

read -r -a flow_args <<< "${FLOWS}"
if [[ ${#flow_args[@]} -eq 0 ]]; then
  echo "ERROR: FLOWS must include at least one flow name" >&2
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

echo "Running flow sweep:"
echo "  flows: ${FLOWS}"
echo "  experiment_id: ${EXPERIMENT_ID}"
echo "  output_root: ${RESULTS_ROOT}"

"${cmd[@]}"

echo "Wrote canonical runs under ${RESULTS_ROOT}/${EXPERIMENT_ID}"
