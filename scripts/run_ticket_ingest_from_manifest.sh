#!/usr/bin/env bash
set -euo pipefail

# Stage 2 wrapper: ingest selected ticket corpus manifest into Chroma.
# Usage:
#   scripts/run_ticket_ingest_from_manifest.sh <selected_manifest> [persist_root] [run_tag]

SELECTED_MANIFEST="${1:?selected manifest path is required}"
PERSIST_ROOT="${2:-./data}"
RUN_TAG="${3:-$(date -u +%Y%m%d)}"

PERSIST_DIR="${PERSIST_ROOT}/servicenow_tickets_balanced_v0_${RUN_TAG}"
MANIFEST_DIR="${PERSIST_ROOT}/manifests"
INGEST_MANIFEST="${MANIFEST_DIR}/servicenow_tickets_balanced_v0_${RUN_TAG}_ingest.json"
COLLECTION_NAME="servicenow_tickets_balanced_v0_${RUN_TAG}"

mkdir -p "${PERSIST_DIR}" "${MANIFEST_DIR}"

echo "Running Stage 2 ticket ingest"
echo "selected_manifest=${SELECTED_MANIFEST}"
echo "persist_dir=${PERSIST_DIR}"
echo "collection=${COLLECTION_NAME}"
echo "ingest_manifest=${INGEST_MANIFEST}"

python scripts/build_tickets_chroma.py \
  --selected-corpus-manifest "${SELECTED_MANIFEST}" \
  --persist-dir "${PERSIST_DIR}" \
  --collection-name "${COLLECTION_NAME}" \
  --manifest-out "${INGEST_MANIFEST}"

echo "done"
echo "collection=${COLLECTION_NAME}"
echo "persist_dir=${PERSIST_DIR}"
echo "ingest_manifest=${INGEST_MANIFEST}"
