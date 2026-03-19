#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${1:-workspace}"

echo "Building M4 derived-ticket retrieval workspace at: ${WORKSPACE_DIR}"

python scripts/build_workspace.py \
  --workspace-dir "${WORKSPACE_DIR}" \
  --chroma-dir data/chroma/aggregates/athos_eval_bundle_20260318_derived_tickets_lt_20250901_v2 \
  --docs-dir data/docs/docs \
  --consulting-docs-dir data/consulting_docs/docs \
  --fs-docs-dir data/docs/docs \
  --fs-consulting-docs-dir data/consulting_docs/docs \
  --fs-tickets-dir data/derived_ticket_corpus/derived_ticket_retrieval_lt_20250901_v2_from_superset_files \
  --fs-include-tickets \
  --build-fs-index
