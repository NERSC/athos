#!/usr/bin/env bash
set -euo pipefail

# Stage 1.5 wrapper: split selected ticket corpus by created-date cutoff.
# Usage:
#   scripts/run_ticket_split_by_date.sh [selected_manifest] [persist_root] [cutoff_date] [run_tag]
#
# Example:
#   scripts/run_ticket_split_by_date.sh \
#     ./data/manifests/servicenow_tickets_balanced_v0_20260305_filter.json \
#     ./data \
#     2026-01-01 \
#     20260305

PERSIST_ROOT="${2:-./data}"
CUTOFF_DATE="${3:-2026-01-01}"
RUN_TAG="${4:-$(date -u +%Y%m%d)}"
SELECTED_MANIFEST="${1:-${PERSIST_ROOT}/manifests/servicenow_tickets_balanced_v0_${RUN_TAG}_filter.json}"

CUTOFF_TAG="${CUTOFF_DATE//-/}"
MANIFEST_DIR="${PERSIST_ROOT}/manifests"
CANDIDATE_ROOT="${PERSIST_ROOT}/servicenow_tickets_balanced_v0_${RUN_TAG}_candidate_ge_${CUTOFF_TAG}"
RETRIEVAL_ROOT="${PERSIST_ROOT}/servicenow_tickets_balanced_v0_${RUN_TAG}_retrieval_lt_${CUTOFF_TAG}"
CANDIDATE_MANIFEST="${MANIFEST_DIR}/servicenow_tickets_balanced_v0_${RUN_TAG}_candidate_ge_${CUTOFF_TAG}_filter.json"
RETRIEVAL_MANIFEST="${MANIFEST_DIR}/servicenow_tickets_balanced_v0_${RUN_TAG}_retrieval_lt_${CUTOFF_TAG}_filter.json"
SPLIT_REPORT="${MANIFEST_DIR}/servicenow_tickets_balanced_v0_${RUN_TAG}_split_${CUTOFF_TAG}_report.json"

mkdir -p "${MANIFEST_DIR}" "${CANDIDATE_ROOT}" "${RETRIEVAL_ROOT}"

echo "Running Stage 1.5 ticket split by created date"
echo "selected_manifest=${SELECTED_MANIFEST}"
echo "cutoff_date=${CUTOFF_DATE}"
echo "candidate_root=${CANDIDATE_ROOT}"
echo "retrieval_root=${RETRIEVAL_ROOT}"
echo "candidate_manifest=${CANDIDATE_MANIFEST}"
echo "retrieval_manifest=${RETRIEVAL_MANIFEST}"
echo "split_report=${SPLIT_REPORT}"

python scripts/split_tickets_by_created_date.py \
  --selected-corpus-manifest "${SELECTED_MANIFEST}" \
  --cutoff-date "${CUTOFF_DATE}" \
  --candidate-output-root "${CANDIDATE_ROOT}" \
  --retrieval-output-root "${RETRIEVAL_ROOT}" \
  --candidate-manifest-out "${CANDIDATE_MANIFEST}" \
  --retrieval-manifest-out "${RETRIEVAL_MANIFEST}" \
  --split-report-out "${SPLIT_REPORT}"

echo "done"
echo "candidate_root=${CANDIDATE_ROOT}"
echo "retrieval_root=${RETRIEVAL_ROOT}"
echo "candidate_manifest=${CANDIDATE_MANIFEST}"
echo "retrieval_manifest=${RETRIEVAL_MANIFEST}"
echo "split_report=${SPLIT_REPORT}"
