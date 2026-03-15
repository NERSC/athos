#!/usr/bin/env bash

set -euo pipefail

# Rerun only "skipped_judge_error" cases from prior mistral judge outputs.
# Defaults target paper-scope expanded datasets that exhibited judge-format skips.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

SCORING_CONFIG_PATH="${SCORING_CONFIG_PATH:-config/paper/cug_m1.yaml}"
JUDGE_MODEL="${JUDGE_MODEL:-mistral_large_3}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
PASSING_SCORE="${PASSING_SCORE:-80}"
JUDGE_MAX_ATTEMPTS="${JUDGE_MAX_ATTEMPTS:-5}"
JUDGE_RETRY_DELAY_MS="${JUDGE_RETRY_DELAY_MS:-1500}"
TICKET_CASES_DIR="${TICKET_CASES_DIR:-data/ticket_cases}"

if [[ ! -f "${SCORING_CONFIG_PATH}" ]]; then
  echo "ERROR: scoring config not found: ${SCORING_CONFIG_PATH}" >&2
  exit 2
fi
if [[ ! -d "${TICKET_CASES_DIR}" ]]; then
  echo "ERROR: missing ticket cases directory: ${TICKET_CASES_DIR}" >&2
  exit 2
fi
if [[ ! -f "evals/nersc_qa.v2.jsonl" ]]; then
  echo "ERROR: missing evals/nersc_qa.v2.jsonl" >&2
  exit 2
fi

TARGETS=(
  "results/cug_m2_canonical|expanded"
  "results/cug_m3_full_sonnet_opt_20260311_081645|expanded"
  "results/cug_m3_20260313_080148|expanded"
  "results/cug_m3_fs_sonnet_stitched_20260314|expanded"
)

rerun_target() {
  local runs_dir="$1"
  local mode="$2"
  local label
  label="$(basename "${runs_dir}")"
  local judge_id="${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}_${label}"
  local skips_file="${runs_dir}/judgments/${judge_id}.skips.jsonl"
  local judgments_out="${runs_dir}/judgments/${judge_id}.jsonl"
  local skips_out="${runs_dir}/judgments/${judge_id}.skips.jsonl"
  local summary_out="${runs_dir}/aggregates/summary.${judge_id}.json"
  local manifest="/tmp/${judge_id}.rerun.manifest.txt"

  if [[ ! -d "${runs_dir}" ]]; then
    echo "WARN: missing runs dir, skipping: ${runs_dir}"
    return
  fi
  if [[ ! -f "${skips_file}" ]]; then
    echo "WARN: missing skips file, skipping: ${skips_file}"
    return
  fi

  jq -r 'select(.reason=="skipped_judge_error") | .run_path' "${skips_file}" | sort -u > "${manifest}"
  local count
  count="$(wc -l < "${manifest}" | tr -d ' ')"
  if [[ "${count}" == "0" ]]; then
    echo "INFO: no skipped_judge_error rows for ${runs_dir}"
    return
  fi

  local ref_args=()
  if [[ "${mode}" == "expanded" ]]; then
    ref_args+=(--cases-dir "${TICKET_CASES_DIR}" --qa-file "evals/nersc_qa.v2.jsonl")
  else
    ref_args+=(--cases-dir "evals/test_cases" --qa-file "evals/simple_qa.jsonl")
  fi

  echo
  echo "==> Rerun ${runs_dir}"
  echo "    judge_id=${judge_id}"
  echo "    skipped_judge_error_cases=${count}"

  python3 evals/score_runs.py \
    --config "${SCORING_CONFIG_PATH}" \
    --runs-manifest "${manifest}" \
    --judge-model "${JUDGE_MODEL}" \
    --judge-id "${judge_id}" \
    --judge-prompt-version "${JUDGE_PROMPT_VERSION}" \
    --passing-score "${PASSING_SCORE}" \
    --judge-max-attempts "${JUDGE_MAX_ATTEMPTS}" \
    --judge-retry-delay-ms "${JUDGE_RETRY_DELAY_MS}" \
    "${ref_args[@]}" \
    --output "${judgments_out}" \
    --skips-output "${skips_out}"

  python3 evals/summarize_results.py \
    --runs-dir "${runs_dir}" \
    --judgment-file "${judgments_out}" \
    --output "${summary_out}"

  echo "    updated judgments: ${judgments_out}"
  echo "    updated summary:   ${summary_out}"
}

for target in "${TARGETS[@]}"; do
  IFS="|" read -r runs_dir mode <<< "${target}"
  rerun_target "${runs_dir}" "${mode}"
done

echo
echo "Done: rerun of skipped_judge_error cases complete."
