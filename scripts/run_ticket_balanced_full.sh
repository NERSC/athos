#!/usr/bin/env bash
set -euo pipefail

# Full balanced two-stage ingestion for CUG-style runs.
# Usage:
#   scripts/run_ticket_balanced_full.sh <source_root> <persist_root> [run_tag]
#
# Example:
#   scripts/run_ticket_balanced_full.sh \
#     /pscratch/sd/s/sfarrell/agentic-ops/get-sn-tickets/servicenow_incidents \
#     /pscratch/sd/s/sfarrell/athos/chroma \
#     20260223

SOURCE_ROOT="${1:-/pscratch/sd/s/sfarrell/agentic-ops/get-sn-tickets/servicenow_incidents}"
PERSIST_ROOT="${2:-/pscratch/sd/s/sfarrell/athos/chroma}"
RUN_TAG="${3:-$(date -u +%Y%m%d)}"

FILTER_MANIFEST="${PERSIST_ROOT}/manifests/servicenow_tickets_balanced_v0_${RUN_TAG}_filter.json"

echo "Running full balanced two-stage ticket ingestion"
echo "source_root=${SOURCE_ROOT}"
echo "persist_root=${PERSIST_ROOT}"
echo "run_tag=${RUN_TAG}"

scripts/run_ticket_filter_balanced_full.sh "${SOURCE_ROOT}" "${PERSIST_ROOT}" "${RUN_TAG}"
scripts/run_ticket_ingest_from_manifest.sh "${FILTER_MANIFEST}" "${PERSIST_ROOT}" "${RUN_TAG}"
