#!/usr/bin/env bash
set -euo pipefail

# Stage 1 wrapper: filter + copy ticket corpus for balanced-mode ingestion.
# Usage:
#   scripts/run_ticket_filter_balanced_full.sh <source_root> <work_root> [run_tag] [close_codes_csv]
# Example close_codes_csv:
#   "Solved (Permanently)"
#   "Solved (Permanently),Solved (Work Around)"

SOURCE_ROOT="${1:-./data/servicenow_incidents}"
WORK_ROOT="${2:-./data}"
RUN_TAG="${3:-$(date -u +%Y%m%d)}"
CLOSE_CODES_CSV="${4:-Solved (Permanently)}"

FILTERED_ROOT="${WORK_ROOT}/servicenow_tickets_balanced_v0_${RUN_TAG}_filtered"
MANIFEST_DIR="${WORK_ROOT}/manifests"
FILTER_MANIFEST="${MANIFEST_DIR}/servicenow_tickets_balanced_v0_${RUN_TAG}_filter.json"

mkdir -p "${FILTERED_ROOT}" "${MANIFEST_DIR}"

INCLUDE_CLOSE_CODE_ARGS=()
IFS=',' read -r -a CLOSE_CODES <<< "${CLOSE_CODES_CSV}"
for code in "${CLOSE_CODES[@]}"; do
  trimmed="$(echo "${code}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  if [[ -n "${trimmed}" ]]; then
    INCLUDE_CLOSE_CODE_ARGS+=(--include-close-code "${trimmed}")
  fi
done

echo "Running Stage 1 ticket filter/copy (balanced)"
echo "source_root=${SOURCE_ROOT}"
echo "filtered_root=${FILTERED_ROOT}"
echo "filter_manifest=${FILTER_MANIFEST}"
echo "include_close_codes=${CLOSE_CODES_CSV}"

python scripts/filter_tickets_corpus.py \
  "${SOURCE_ROOT}" \
  --output-root "${FILTERED_ROOT}" \
  --mode balanced \
  "${INCLUDE_CLOSE_CODE_ARGS[@]}" \
  --manifest-out "${FILTER_MANIFEST}"

echo "done"
echo "filtered_root=${FILTERED_ROOT}"
echo "filter_manifest=${FILTER_MANIFEST}"
