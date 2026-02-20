#!/usr/bin/env bash

set -euo pipefail

# Minimal end-to-end smoke test for eval pipeline v2.
# Override these with env vars if needed.
FLOW_NAME="${FLOW_NAME:-lang_chat}"
JUDGE_MODEL="${JUDGE_MODEL:-cborg_coder}"
JUDGE_ID="${JUDGE_ID:-${JUDGE_MODEL}_rubric_v1}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
RUN_COUNT="${RUN_COUNT:-1}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
LOGS_ROOT="${LOGS_ROOT:-logs}"

experiment_id="smoke_$(date +%Y%m%d_%H%M%S)"
runs_dir="${RESULTS_ROOT}/${experiment_id}"
summary_out="${LOGS_ROOT}/eval_results_${experiment_id}.json"
judgments_out="${runs_dir}/judgments/${JUDGE_ID}.jsonl"
skips_out="${runs_dir}/judgments/${JUDGE_ID}.skips.jsonl"
aggregates_out="${runs_dir}/aggregates/summary.json"

mkdir -p "${LOGS_ROOT}"

echo "==> [1/3] Generating canonical runs (execution only)"
python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow "${FLOW_NAME}" \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --output-dir "${RESULTS_ROOT}" \
  --experiment-id "${experiment_id}" \
  --run-count "${RUN_COUNT}" \
  --output "${summary_out}"

echo "==> [2/3] Scoring canonical runs"
python evals/score_runs.py \
  --config config/config.yaml \
  --runs-dir "${runs_dir}" \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --judge-model "${JUDGE_MODEL}" \
  --judge-id "${JUDGE_ID}" \
  --judge-prompt-version "${JUDGE_PROMPT_VERSION}" \
  --fail-on-skip \
  --skips-output "${skips_out}" \
  --output "${judgments_out}"

echo "==> [3/3] Summarizing runs + judgments"
python evals/summarize_results.py \
  --runs-dir "${runs_dir}" \
  --judgments-dir "${runs_dir}/judgments" \
  --output "${aggregates_out}"

echo
echo "Smoke run complete. Review outputs:"
echo "  Experiment ID: ${experiment_id}"
echo "  Canonical runs root: ${runs_dir}"
echo "  Legacy summary JSON: ${summary_out}"
echo "  Judgments JSONL: ${judgments_out}"
echo "  Skips JSONL: ${skips_out}"
echo "  Aggregates summary: ${aggregates_out}"

echo
echo "Quick counts:"
python - "$judgments_out" "$skips_out" <<'PY'
import collections
import json
import pathlib
import sys

judgments_path = pathlib.Path(sys.argv[1])
skips_path = pathlib.Path(sys.argv[2])

judgments = []
if judgments_path.exists():
    for line in judgments_path.read_text().splitlines():
        if line.strip():
            judgments.append(json.loads(line))

status_counts = collections.Counter(
    j.get("judgment_status", "unknown") for j in judgments
)
scored_count = status_counts.get("scored", 0)
skipped_count = sum(
    count for status, count in status_counts.items() if str(status).startswith("skipped_")
)

print(f"  Judgments total: {len(judgments)}")
print(f"  Scored: {scored_count}")
print(f"  Skipped: {skipped_count}")
if status_counts:
    print("  Judgment status breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"    - {status}: {count}")

if skips_path.exists():
    skips = []
    for line in skips_path.read_text().splitlines():
        if line.strip():
            skips.append(json.loads(line))
    reason_counts = collections.Counter(s.get("reason", "unknown") for s in skips)
    print(f"  Skip records: {len(skips)}")
    if reason_counts:
        print("  Skip reason breakdown:")
        for reason, count in sorted(reason_counts.items()):
            print(f"    - {reason}: {count}")
else:
    print("  Skip records: 0 (no skips file found)")
PY
