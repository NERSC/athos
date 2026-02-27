#!/usr/bin/env bash
set -euo pipefail

SPEC_PATH="${1:-config/chroma_aggregate_spec.yaml}"

echo "Running Chroma aggregate build with spec: ${SPEC_PATH}"
python scripts/build_chroma_aggregate.py --spec "${SPEC_PATH}"
