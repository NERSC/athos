#!/usr/bin/env bash

set -euo pipefail

# Render the focused harness comparison table (ATHOS harness rows + external coding-agent rows).
#
# Defaults:
# - ATHOS harness summary: results/cug_m3_var_20260311_231139/aggregates/summary.json
# - Codex external summary: results/cug_codex_external_mini_20260313_232712/aggregates/summary.json
# - Claude external summary: results/cug_claude_external_mini_20260314/aggregates/summary.json
# - Output table: ../athos_cug_2026_paper/tables/cug_harness_comparison.tex
#
# Example:
#   scripts/render_cug_harness_comparison_table.sh
#   ATHOS_SUMMARY=results/<exp>/aggregates/summary.json \
#   CODEX_SUMMARY=results/<exp>/aggregates/summary.json \
#   CLAUDE_SUMMARY=results/<exp>/aggregates/summary.json \
#   scripts/render_cug_harness_comparison_table.sh

ATHOS_SUMMARY="${ATHOS_SUMMARY:-results/cug_m3_var_20260311_231139/aggregates/summary.json}"
CODEX_SUMMARY="${CODEX_SUMMARY:-results/cug_codex_external_mini_20260313_232712/aggregates/summary.json}"
CLAUDE_SUMMARY="${CLAUDE_SUMMARY:-results/cug_claude_external_mini_20260314/aggregates/summary.json}"
OUTPUT_TEX="${OUTPUT_TEX:-../athos_cug_2026_paper/tables/cug_harness_comparison.tex}"
TABLE_LABEL="${TABLE_LABEL:-tab:cug-harness-comparison}"
TABLE_CAPTION="${TABLE_CAPTION:-Focused Harness Comparison on Auxiliary Small-Scale Q\\&A and Ticket Sets (Tokens I/O/T = mean input/output/total tokens per run; Lat = median end-to-end latency).}"

for path in "${ATHOS_SUMMARY}" "${CODEX_SUMMARY}" "${CLAUDE_SUMMARY}"; do
  if [[ ! -f "${path}" ]]; then
    echo "ERROR: summary file not found: ${path}" >&2
    exit 2
  fi
done

echo "Rendering harness comparison table"
echo "  athos_summary: ${ATHOS_SUMMARY}"
echo "  codex_summary: ${CODEX_SUMMARY}"
echo "  claude_summary: ${CLAUDE_SUMMARY}"
echo "  output_tex: ${OUTPUT_TEX}"

python3 scripts/render_harness_comparison_table.py \
  --summary-json "${ATHOS_SUMMARY}" \
  --summary-json "${CODEX_SUMMARY}" \
  --summary-json "${CLAUDE_SUMMARY}" \
  --output-tex "${OUTPUT_TEX}" \
  --caption "${TABLE_CAPTION}" \
  --label "${TABLE_LABEL}"

echo "Done."
