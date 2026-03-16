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
OUTPUT_DIR="${OUTPUT_DIR:-../athos_cug_2026_paper/figures}"
SHOW_FAILURE_COUNTS="${SHOW_FAILURE_COUNTS:-0}"

GPTOSS_JUDGMENTS="${GPTOSS_JUDGMENTS:-${GPTOSS_RUN_DIR}/judgments/llama_4_maverick_rubric_v1_cug_m3_var_20260312_093435.jsonl}"
SONNET_JUDGMENTS="${SONNET_JUDGMENTS:-${SONNET_RUN_DIR}/judgments/llama_4_maverick_rubric_v1_cug_m3_var_20260312_130318.jsonl}"

mkdir -p "${OUTPUT_DIR}"

echo "Rendering GPT-OSS variance plot"
if [[ "${SHOW_FAILURE_COUNTS}" == "1" ]]; then
  python scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${GPTOSS_JUDGMENTS}" \
    --output "${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / GPT-OSS" \
    --show-failure-counts
else
  python scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${GPTOSS_JUDGMENTS}" \
    --output "${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / GPT-OSS"
fi

echo "Rendering Claude Sonnet variance plot"
if [[ "${SHOW_FAILURE_COUNTS}" == "1" ]]; then
  python scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${SONNET_JUDGMENTS}" \
    --output "${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / Claude Sonnet" \
    --show-failure-counts
else
  python scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${SONNET_JUDGMENTS}" \
    --output "${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / Claude Sonnet"
fi

echo "Done."
echo "  ${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf"
echo "  ${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf"
