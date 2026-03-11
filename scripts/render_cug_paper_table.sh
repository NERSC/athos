#!/usr/bin/env bash

set -euo pipefail

# Render merged paper per-config table from one or more run/judgment sources.
#
# Source format:
#   RUN_SOURCES="runs_dir::judgments_dir [runs_dir::judgments_dir ...]"
#
# Defaults currently target M2 canonical only, but are designed for M3+ appends.
#
# Examples:
#   scripts/render_cug_paper_table.sh
#   RUN_SOURCES="results/cug_m2_canonical::results/cug_m2_canonical/judgments results/cug_m3_part_a::results/cug_m3_part_a/judgments results/cug_m3_part_b::results/cug_m3_part_b/judgments" scripts/render_cug_paper_table.sh

# Preferred default is a checked-in source manifest; RUN_SOURCES env var overrides it.
SOURCE_MANIFEST="${SOURCE_MANIFEST:-config/paper/cug_paper_table_sources.txt}"
RUN_SOURCES="${RUN_SOURCES:-}"
ALLOW_MIXED_JUDGES="${ALLOW_MIXED_JUDGES:-1}"

SUMMARY_DIR="${SUMMARY_DIR:-results/cug_paper_table/summaries}"
MERGED_SUMMARY_OUT="${MERGED_SUMMARY_OUT:-results/cug_paper_table/summary_inputs.manifest.txt}"
TABLE_OUT="${TABLE_OUT:-results/cug_paper_table/per_config_results_table.tex}"

TABLE_CAPTION="${TABLE_CAPTION:-Per-Configuration Results on NERSC QA and Ticket Datasets (Tokens I/O/T = mean input/output/total tokens per run; Lat = median end-to-end latency)}"
TABLE_LABEL="${TABLE_LABEL:-tab:cug-results-per-config}"

INCLUDE_DATASETS="${INCLUDE_DATASETS:-nersc_qa.v2 ticket_cases}"
DATASET_ORDER="${DATASET_ORDER:-}"
INCLUDE_CONFIG_SUBSTRINGS="${INCLUDE_CONFIG_SUBSTRINGS:-}"
EXCLUDE_ZERO_SCORED="${EXCLUDE_ZERO_SCORED:-0}"

mkdir -p "${SUMMARY_DIR}" "$(dirname "${MERGED_SUMMARY_OUT}")" "$(dirname "${TABLE_OUT}")"

summary_paths=()
source_index=0

if [[ -z "${RUN_SOURCES}" ]]; then
  if [[ ! -f "${SOURCE_MANIFEST}" ]]; then
    echo "ERROR: RUN_SOURCES is empty and source manifest not found: ${SOURCE_MANIFEST}" >&2
    exit 2
  fi
  RUN_SOURCES="$(awk 'NF && $1 !~ /^#/' "${SOURCE_MANIFEST}" | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
fi

read -r -a source_arr <<< "${RUN_SOURCES}"
if [[ ${#source_arr[@]} -eq 0 ]]; then
  echo "ERROR: no valid sources found in RUN_SOURCES or ${SOURCE_MANIFEST}." >&2
  exit 2
fi

echo "Rendering paper table"
echo "  source_manifest: ${SOURCE_MANIFEST}"
echo "  run_sources: ${RUN_SOURCES}"
echo "  allow_mixed_judges: ${ALLOW_MIXED_JUDGES}"
echo "  summary_dir: ${SUMMARY_DIR}"
echo "  table_out: ${TABLE_OUT}"
echo

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

  summary_out="${SUMMARY_DIR}/summary_${source_index}.json"
  source_index=$((source_index + 1))

  summary_cmd=(
    python evals/summarize_results.py
    --runs-dir "${runs_dir}"
    --judgments-dir "${judgments_dir}"
    --output "${summary_out}"
  )
  if [[ "${ALLOW_MIXED_JUDGES}" == "1" ]]; then
    summary_cmd+=(--allow-mixed-judges)
  fi

  echo "Summarizing source ${source_index}:"
  echo "  runs_dir: ${runs_dir}"
  echo "  judgments_dir: ${judgments_dir}"
  echo "  summary_out: ${summary_out}"
  "${summary_cmd[@]}"
  echo

  summary_paths+=("${summary_out}")
done

printf "%s\n" "${summary_paths[@]}" > "${MERGED_SUMMARY_OUT}"

render_cmd=(
  python scripts/render_per_config_results_table.py
  --output-tex "${TABLE_OUT}"
  --caption "${TABLE_CAPTION}"
  --label "${TABLE_LABEL}"
)

for summary_path in "${summary_paths[@]}"; do
  render_cmd+=(--summary-json "${summary_path}")
done

read -r -a include_dataset_arr <<< "${INCLUDE_DATASETS}"
for dataset_id in "${include_dataset_arr[@]}"; do
  [[ -z "${dataset_id}" ]] && continue
  render_cmd+=(--include-dataset "${dataset_id}")
done

if [[ -n "${DATASET_ORDER}" ]]; then
  read -r -a dataset_order_arr <<< "${DATASET_ORDER}"
  for dataset_id in "${dataset_order_arr[@]}"; do
    [[ -z "${dataset_id}" ]] && continue
    render_cmd+=(--dataset-order "${dataset_id}")
  done
fi

read -r -a include_cfg_arr <<< "${INCLUDE_CONFIG_SUBSTRINGS}"
for cfg_substr in "${include_cfg_arr[@]}"; do
  [[ -z "${cfg_substr}" ]] && continue
  render_cmd+=(--include-config-substring "${cfg_substr}")
done

if [[ "${EXCLUDE_ZERO_SCORED}" == "1" ]]; then
  render_cmd+=(--exclude-zero-scored)
fi

echo "Rendering merged table"
echo "  include_datasets: ${INCLUDE_DATASETS}"
echo "  dataset_order: ${DATASET_ORDER}"
if [[ -n "${INCLUDE_CONFIG_SUBSTRINGS}" ]]; then
  echo "  include_config_substrings: ${INCLUDE_CONFIG_SUBSTRINGS}"
fi
"${render_cmd[@]}"
echo

echo "Done."
echo "  Summary manifest: ${MERGED_SUMMARY_OUT}"
echo "  Table: ${TABLE_OUT}"
