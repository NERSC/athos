#!/usr/bin/env bash

set -euo pipefail

# Render per-case variance plots as one PDF per config so LaTeX can arrange
# them as subfigures later.
#
# Usage:
#   scripts/render_cug_variance_case_plots.sh
#   VAR_RUN_DIR=results/cug_m4_var \
#   scripts/render_cug_variance_case_plots.sh

VAR_RUN_DIR="${VAR_RUN_DIR:-results/cug_m4_var}"
OUTPUT_DIR="${OUTPUT_DIR:-../athos_cug_2026_paper/figures}"
SHOW_FAILURE_COUNTS="${SHOW_FAILURE_COUNTS:-0}"
PYTHON_BIN="${PYTHON_BIN:-}"

VAR_JUDGMENTS="${VAR_JUDGMENTS:-${VAR_RUN_DIR}/judgments/llama_4_maverick_rubric_v1.jsonl}"
GPTOSS_CONFIG_SUBSTRING="${GPTOSS_CONFIG_SUBSTRING:-cug_lang_chroma_gptoss_opt}"
SONNET_CONFIG_SUBSTRING="${SONNET_CONFIG_SUBSTRING:-cug_lang_chroma_sonnet_opt}"

if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x ".venv/bin/python3" ]]; then
    PYTHON_BIN=".venv/bin/python3"
  else
    PYTHON_BIN="python3"
  fi
fi

mkdir -p "${OUTPUT_DIR}"

echo "Rendering GPT-OSS variance plot"
if [[ "${SHOW_FAILURE_COUNTS}" == "1" ]]; then
  "${PYTHON_BIN}" scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${VAR_JUDGMENTS}" \
    --config-substring "${GPTOSS_CONFIG_SUBSTRING}" \
    --output "${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / GPT-OSS" \
    --show-failure-counts
else
  "${PYTHON_BIN}" scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${VAR_JUDGMENTS}" \
    --config-substring "${GPTOSS_CONFIG_SUBSTRING}" \
    --output "${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / GPT-OSS"
fi

echo "Rendering Claude Sonnet variance plot"
if [[ "${SHOW_FAILURE_COUNTS}" == "1" ]]; then
  "${PYTHON_BIN}" scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${VAR_JUDGMENTS}" \
    --config-substring "${SONNET_CONFIG_SUBSTRING}" \
    --output "${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / Claude Sonnet" \
    --show-failure-counts
else
  "${PYTHON_BIN}" scripts/plot_cug_variance_by_case.py \
    --judgments-jsonl "${VAR_JUDGMENTS}" \
    --config-substring "${SONNET_CONFIG_SUBSTRING}" \
    --output "${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf" \
    --title "Per-Case Score Variance: LangChain / Claude Sonnet"
fi

echo "Done."
echo "  ${OUTPUT_DIR}/cug_variance_gptoss_by_case.pdf"
echo "  ${OUTPUT_DIR}/cug_variance_sonnet_by_case.pdf"
