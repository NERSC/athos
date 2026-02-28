#!/usr/bin/env bash
set -euo pipefail

# Full balanced ingestion for CUG-style runs.
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

PERSIST_DIR="${PERSIST_ROOT}/servicenow_tickets_balanced_v0_${RUN_TAG}"
MANIFEST_DIR="${PERSIST_ROOT}/manifests"
MANIFEST_PATH="${MANIFEST_DIR}/servicenow_tickets_balanced_v0_${RUN_TAG}.json"
COLLECTION_NAME="servicenow_tickets_balanced_v0_${RUN_TAG}"

mkdir -p "${PERSIST_DIR}" "${MANIFEST_DIR}"

echo "Running full balanced ticket ingestion"
echo "source_root=${SOURCE_ROOT}"
echo "persist_dir=${PERSIST_DIR}"
echo "collection=${COLLECTION_NAME}"
echo "manifest=${MANIFEST_PATH}"

CMD=(
  python scripts/build_tickets_chroma.py
  "${SOURCE_ROOT}"
  --persist-dir "${PERSIST_DIR}"
  --collection-name "${COLLECTION_NAME}"
  --mode balanced
  --manifest-out "${MANIFEST_PATH}"
)

echo "command:"
printf '  %q' "${CMD[@]}"
printf '\n'

"${CMD[@]}"

echo "done"
echo "collection=${COLLECTION_NAME}"
echo "persist_dir=${PERSIST_DIR}"
echo "manifest=${MANIFEST_PATH}"
