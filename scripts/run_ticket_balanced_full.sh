#!/usr/bin/env bash
set -euo pipefail

# Full balanced ingestion for CUG-style runs.
# Usage:
#   scripts/run_ticket_balanced_full.sh <source_root> <persist_root> [run_tag] [close_codes_csv] [cutoff_date] [chroma_root]
#
# Example:
#   scripts/run_ticket_balanced_full.sh \
#     /path/to/servicenow_incidents \
#     /path/to/athos/data \
#     20260303 \
#     "Solved (Permanently)" \
#     2025-09-01 \
#     /path/to/athos/data/chroma

SOURCE_ROOT="${1:-./data/servicenow_incidents}"
PERSIST_ROOT="${2:-./data}"
RUN_TAG="${3:-$(date -u +%Y%m%d)}"
CLOSE_CODES_CSV="${4:-Solved (Permanently)}"
CUTOFF_DATE="${5:-2025-09-01}"
CHROMA_ROOT="${6:-${PERSIST_ROOT}/chroma}"

FILTER_MANIFEST="${PERSIST_ROOT}/manifests/servicenow_tickets_balanced_v0_${RUN_TAG}_filter.json"

echo "Running full balanced two-stage ticket ingestion"
echo "source_root=${SOURCE_ROOT}"
echo "persist_root=${PERSIST_ROOT}"
echo "run_tag=${RUN_TAG}"
echo "include_close_codes=${CLOSE_CODES_CSV}"
echo "chroma_root=${CHROMA_ROOT}"
if [[ -n "${CUTOFF_DATE}" ]]; then
  echo "split_cutoff_date=${CUTOFF_DATE}"
fi

time scripts/run_ticket_filter_balanced_full.sh "${SOURCE_ROOT}" "${PERSIST_ROOT}" "${RUN_TAG}" "${CLOSE_CODES_CSV}"
if [[ -n "${CUTOFF_DATE}" ]]; then
  time scripts/run_ticket_split_by_date.sh "${FILTER_MANIFEST}" "${PERSIST_ROOT}" "${CUTOFF_DATE}" "${RUN_TAG}"
  CUTOFF_TAG="${CUTOFF_DATE//-/}"
  RETRIEVAL_MANIFEST="${PERSIST_ROOT}/manifests/servicenow_tickets_balanced_v0_${RUN_TAG}_retrieval_lt_${CUTOFF_TAG}_filter.json"
  INGEST_RUN_TAG="${RUN_TAG}_retrieval_lt_${CUTOFF_TAG}"
  time scripts/run_ticket_ingest_from_manifest.sh "${RETRIEVAL_MANIFEST}" "${CHROMA_ROOT}" "${INGEST_RUN_TAG}"
else
  time scripts/run_ticket_ingest_from_manifest.sh "${FILTER_MANIFEST}" "${CHROMA_ROOT}" "${RUN_TAG}"
fi
