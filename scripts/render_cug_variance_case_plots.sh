#!/usr/bin/env bash

set -euo pipefail

# Render per-case variance plots as one PDF per config so LaTeX can arrange
# them as subfigures later.
#
# Usage:
#   scripts/render_cug_variance_case_plots.sh
#   GPTOSS_RUN_DIR=results/cug_m3_var_20260312_093435 \
#   SONNET_RUN_DIR=results/cug_m3_var_20260312_130318 \
#   scripts/render_cug_variance_case_plots.sh

GPTOSS_RUN_DIR="${GPTOSS_RUN_DIR:-results/cug_m3_var_20260312_093435}"
SONNET_RUN_DIR="${SONNET_RUN_DIR:-results/cug_m3_var_20260312_130318}"
OUTPUT_DIR="${OUTPUT_DIR:-results/cug_variance_figures}"
SHOW_FAILURE_COUNTS="${SHOW_FAILURE_COUNTS:-0}"

GPTOSS_JUDGMENTS="${GPTOSS_JUDGMENTS:-${GPTOSS_RUN_DIR}/judgments/gptoss_rubric_v1.jsonl}"
SONNET_JUDGMENTS="${SONNET_JUDGMENTS:-${SONNET_RUN_DIR}/judgments/gptoss_rubric_v1.jsonl}"

mkdir -p "${OUTPUT_DIR}"

common_args=()
if [[ "${SHOW_FAILURE_COUNTS}" == "1" ]]; then
  common_args+=(--show-failure-counts)
fi

echo "Rendering GPT-OSS variance plot"
python scripts/plot_cug_variance_by_case.py \
  --judgments-jsonl "${GPTOSS_JUDGMENTS}" \
  --output "${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf" \
  --title "Per-Case Score Variance: LangChain / GPT-OSS" \
  "${common_args[@]}"

echo "Rendering Claude Sonnet variance plot"
python scripts/plot_cug_variance_by_case.py \
  --judgments-jsonl "${SONNET_JUDGMENTS}" \
  --output "${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf" \
  --title "Per-Case Score Variance: LangChain / Claude Sonnet" \
  "${common_args[@]}"

echo "Done."
echo "  ${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf"
echo "  ${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf"
