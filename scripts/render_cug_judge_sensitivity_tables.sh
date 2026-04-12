#!/usr/bin/env bash

set -euo pipefail

# Render lightweight judge-sensitivity tables for paper writeup.
#
# This script:
# 1) Regenerates per-judge summaries for the canonical paper source manifest.
# 2) Renders three LaTeX tables:
#    - leniency ladder
#    - ranking stability
#    - deltas vs Maverick

SOURCE_MANIFEST="${SOURCE_MANIFEST:-config/paper/cug_paper_table_sources.txt}"
RUN_SOURCES="${RUN_SOURCES:-}"
JUDGES="${JUDGES:-gptoss llama_4_maverick mistral_large_3}"

SUMMARY_ROOT="${SUMMARY_ROOT:-results/judge_sensitivity/summaries}"
TABLE_OUT_DIR="${TABLE_OUT_DIR:-../athos_cug_2026_paper/tables}"

mkdir -p "${SUMMARY_ROOT}" "${TABLE_OUT_DIR}"

if [[ -z "${RUN_SOURCES}" ]]; then
  if [[ ! -f "${SOURCE_MANIFEST}" ]]; then
    echo "ERROR: RUN_SOURCES is empty and source manifest not found: ${SOURCE_MANIFEST}" >&2
    exit 2
  fi
  RUN_SOURCES="$(awk 'NF && $1 !~ /^#/' "${SOURCE_MANIFEST}" | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
fi

read -r -a source_arr <<< "${RUN_SOURCES}"
read -r -a judge_arr <<< "${JUDGES}"

if [[ ${#source_arr[@]} -eq 0 ]]; then
  echo "ERROR: no valid sources found." >&2
  exit 2
fi
if [[ ${#judge_arr[@]} -eq 0 ]]; then
  echo "ERROR: no judges specified." >&2
  exit 2
fi

echo "Rendering CUG judge sensitivity tables"
echo "  source_manifest: ${SOURCE_MANIFEST}"
echo "  run_sources: ${RUN_SOURCES}"
echo "  judges: ${JUDGES}"
echo "  summary_root: ${SUMMARY_ROOT}"
echo "  table_out_dir: ${TABLE_OUT_DIR}"
echo

for judge in "${judge_arr[@]}"; do
  judge_dir="${SUMMARY_ROOT}/${judge}"
  mkdir -p "${judge_dir}"
  rm -f "${judge_dir}"/summary_*.json
done

# 1) Build per-judge summaries.
source_index=0
for source_spec in "${source_arr[@]}"; do
  runs_dir="${source_spec%%::*}"
  judgments_dir="${source_spec#*::}"

  if [[ -z "${runs_dir}" || -z "${judgments_dir}" || "${runs_dir}" == "${judgments_dir}" ]]; then
    echo "ERROR: invalid source spec '${source_spec}'. Expected runs_dir::judgments_dir." >&2
    exit 2
  fi
  if [[ ! -d "${runs_dir}" ]]; then
    echo "ERROR: runs dir not found: ${runs_dir}" >&2
    exit 2
  fi
  if [[ ! -d "${judgments_dir}" ]]; then
    echo "ERROR: judgments dir not found: ${judgments_dir}" >&2
    exit 2
  fi

  for judge in "${judge_arr[@]}"; do
    judge_dir="${SUMMARY_ROOT}/${judge}"
    out="${judge_dir}/summary_${source_index}.json"

    echo "Summarizing source ${source_index} for judge=${judge}"
    python3 evals/summarize_results.py \
      --runs-dir "${runs_dir}" \
      --judgments-dir "${judgments_dir}" \
      --judge-model "${judge}" \
      --allow-mixed-judges \
      --output "${out}"
  done

  source_index=$((source_index + 1))
done

echo
# 2) Render tables.
render_cmd=(
  python3 scripts/render_judge_sensitivity_tables.py
  --summary-root "${SUMMARY_ROOT}"
  --output-dir "${TABLE_OUT_DIR}"
  --source-config-filter "0::base"
  --source-config-filter "1::filesystem,chroma"
)
for judge in "${judge_arr[@]}"; do
  render_cmd+=(--judge "${judge}")
done

"${render_cmd[@]}"

echo
echo "Done."
echo "  ${TABLE_OUT_DIR}/cug_judge_leniency_ladder.tex"
echo "  ${TABLE_OUT_DIR}/cug_judge_ranking_stability.tex"
echo "  ${TABLE_OUT_DIR}/cug_judge_deltas.tex"
