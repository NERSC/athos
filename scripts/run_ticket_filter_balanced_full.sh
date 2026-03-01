#!/usr/bin/env bash
set -euo pipefail

# Stage 1 wrapper: filter + copy ticket corpus for balanced-mode ingestion.
# Usage:
#   scripts/run_ticket_filter_balanced_full.sh <source_root> <work_root> [run_tag]

SOURCE_ROOT="${1:-/pscratch/sd/s/sfarrell/agentic-ops/get-sn-tickets/servicenow_incidents}"
WORK_ROOT="${2:-/pscratch/sd/s/sfarrell/athos/chroma}"
RUN_TAG="${3:-$(date -u +%Y%m%d)}"

FILTERED_ROOT="${WORK_ROOT}/servicenow_tickets_balanced_v0_${RUN_TAG}_filtered"
MANIFEST_DIR="${WORK_ROOT}/manifests"
FILTER_MANIFEST="${MANIFEST_DIR}/servicenow_tickets_balanced_v0_${RUN_TAG}_filter.json"

mkdir -p "${FILTERED_ROOT}" "${MANIFEST_DIR}"

echo "Running Stage 1 ticket filter/copy (balanced)"
echo "source_root=${SOURCE_ROOT}"
echo "filtered_root=${FILTERED_ROOT}"
echo "filter_manifest=${FILTER_MANIFEST}"

python scripts/filter_tickets_corpus.py \
  "${SOURCE_ROOT}" \
  --output-root "${FILTERED_ROOT}" \
  --mode balanced \
  --manifest-out "${FILTER_MANIFEST}"

echo "done"
echo "filtered_root=${FILTERED_ROOT}"
echo "filter_manifest=${FILTER_MANIFEST}"
