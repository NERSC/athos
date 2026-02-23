#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="${1:-/pscratch/sd/s/sfarrell/agentic-ops/get-sn-tickets/servicenow_incidents}"
TARGET_KEPT="${2:-500}"
WORK_ROOT="${3:-/tmp/ticket_balanced_smoke}"

PERSIST_DIR="${WORK_ROOT}/chroma_${TARGET_KEPT}"
COLLECTION_NAME="servicenow_tickets_balanced_smoke_${TARGET_KEPT}"
MANIFEST_PATH="${WORK_ROOT}/manifest_${TARGET_KEPT}.json"

echo "source_root=${SOURCE_ROOT}"
echo "target_kept=${TARGET_KEPT}"
echo "work_root=${WORK_ROOT}"

python scripts/build_tickets_chroma.py \
  "${SOURCE_ROOT}" \
  --persist-dir "${PERSIST_DIR}" \
  --collection-name "${COLLECTION_NAME}" \
  --mode balanced \
  --limit "${TARGET_KEPT}" \
  --manifest-out "${MANIFEST_PATH}"

python - <<PY
import chromadb

persist_dir = ${PERSIST_DIR@Q}
collection = ${COLLECTION_NAME@Q}
client = chromadb.PersistentClient(path=persist_dir)
col = client.get_collection(collection)
queries = [
    "python package import error on login node",
    "quota exceeded in home directory",
    "gpu job failure slurm",
]
for q in queries:
    res = col.query(query_texts=[q], n_results=3)
    ids = res.get("ids", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    print(f"QUERY: {q}")
    for i, (doc_id, meta) in enumerate(zip(ids, metas), start=1):
        incident = (meta or {}).get("incident_number")
        category = (meta or {}).get("category")
        contact = (meta or {}).get("contact_type")
        print(f"  {i}. id={doc_id} incident={incident} category={category} contact_type={contact}")
PY

echo "manifest=${MANIFEST_PATH}"
echo "persist_dir=${PERSIST_DIR}"
echo "collection=${COLLECTION_NAME}"
