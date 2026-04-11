#!/usr/bin/env bash

set -euo pipefail

# Master rescoring wrapper for paper-scope CUG artifacts.
# Uses an explicit canonical target list to avoid accidentally scoring all historical runs.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

SCORING_CONFIG_PATH="${SCORING_CONFIG_PATH:-config/paper/cug_m1.yaml}"
JUDGE_MODEL="${JUDGE_MODEL:-mistral_large_3}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
JUDGE_ID_PREFIX="${JUDGE_ID_PREFIX:-${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}}"
PASSING_SCORE="${PASSING_SCORE:-80}"
JUDGE_MAX_ATTEMPTS="${JUDGE_MAX_ATTEMPTS:-3}"
JUDGE_RETRY_DELAY_MS="${JUDGE_RETRY_DELAY_MS:-1000}"
CHECK_BUDGET="${CHECK_BUDGET:-1}"
TICKET_CASES_DIR="${TICKET_CASES_DIR:-./data/ticket_cases}"
TARGET_SET="${TARGET_SET:-m4_paper_sensitivity}"

if [[ ! -f "${SCORING_CONFIG_PATH}" ]]; then
  echo "ERROR: scoring config not found: ${SCORING_CONFIG_PATH}" >&2
  exit 2
fi

if [[ ! -f "evals/nersc_qa.v2.jsonl" ]]; then
  echo "ERROR: missing evals/nersc_qa.v2.jsonl" >&2
  exit 2
fi
if [[ ! -f "evals/simple_qa.jsonl" ]]; then
  echo "ERROR: missing evals/simple_qa.jsonl" >&2
  exit 2
fi
if [[ ! -d "evals/test_cases" ]]; then
  echo "ERROR: missing evals/test_cases" >&2
  exit 2
fi
if [[ ! -d "${TICKET_CASES_DIR}" ]]; then
  echo "ERROR: missing ticket cases directory: ${TICKET_CASES_DIR}" >&2
  exit 2
fi

#if [[ -z "${AMSC_I2_API_KEY:-}" || -z "${AMSC_I2_API_URL:-}" ]]; then
#  echo "ERROR: AMSC_I2_API_KEY / AMSC_I2_API_URL are not set. Run 'source ~/.bash_aliases; setup_i2api' first." >&2
#  exit 2
#fi

TARGETS=()

set_targets() {
  case "${TARGET_SET}" in
    m4)
      TARGETS=(
        "results/cug_m4|expanded"
      )
      ;;
    m4_paper_sensitivity)
      TARGETS=(
        "results/cug_m4|expanded"
        "results/cug_m4_var|mini"
        "results/cug_m4_harness|mini"
        "results/cug_m4_harness_lang_sonnet_opt_mini_20260329|mini"
        "results/cug_m4_harness_smol_sonnet_mini_20260329|mini"
        "results/cug_codex_external_full_20260329|mini"
        "results/cug_claude_external_full_20260329|mini"
      )
      ;;
    legacy_paper)
      TARGETS=(
        "results/cug_m2_canonical|expanded"
        "results/cug_m3_full_gptoss_opt_20260311_013848|expanded"
        "results/cug_m3_full_sonnet_opt_20260311_081645|expanded"
        "results/cug_m3_20260313_080148|expanded"
        "results/cug_m3_fs_sonnet_stitched_20260314|expanded"
        "results/cug_codex_external_mini_20260313_232712|mini"
        "results/cug_claude_external_mini_20260314|mini"
      )
      ;;
    all_paper)
      TARGETS=(
        "results/cug_m4|expanded"
        "results/cug_m2_canonical|expanded"
        "results/cug_m3_full_gptoss_opt_20260311_013848|expanded"
        "results/cug_m3_full_sonnet_opt_20260311_081645|expanded"
        "results/cug_m3_20260313_080148|expanded"
        "results/cug_m3_fs_sonnet_stitched_20260314|expanded"
        "results/cug_codex_external_mini_20260313_232712|mini"
        "results/cug_claude_external_mini_20260314|mini"
      )
      ;;
    *)
      echo "ERROR: unknown TARGET_SET='${TARGET_SET}'" >&2
      echo "Valid options: m4, m4_paper_sensitivity, legacy_paper, all_paper" >&2
      exit 2
      ;;
  esac
}

print_budget() {
  if [[ "${CHECK_BUDGET}" != "1" ]]; then
    return
  fi
  if command -v check_i2api_usage >/dev/null 2>&1; then
    echo "==> i2 budget snapshot"
    check_i2api_usage || true
  fi
}

set_targets
echo "==> target_set=${TARGET_SET}"

score_target() {
  local runs_dir="$1"
  local mode="$2"
  local target_index="$3"
  local target_total="$4"
  local label
  label="$(basename "${runs_dir}")"
  local judge_id="${JUDGE_ID_PREFIX}_${label}"
  local judgments_dir="${runs_dir}/judgments"
  local aggregates_dir="${runs_dir}/aggregates"
  local judgments_out="${judgments_dir}/${judge_id}.jsonl"
  local skips_out="${judgments_dir}/${judge_id}.skips.jsonl"
  local summary_out="${aggregates_dir}/summary.${judge_id}.json"

  if [[ ! -d "${runs_dir}" ]]; then
    echo "WARN: skipping missing runs dir: ${runs_dir}"
    return
  fi

  mkdir -p "${judgments_dir}" "${aggregates_dir}"

  local ref_args=()
  if [[ "${mode}" == "expanded" ]]; then
    ref_args+=(--cases-dir "${TICKET_CASES_DIR}" --qa-file "evals/nersc_qa.v2.jsonl")
  elif [[ "${mode}" == "mini" ]]; then
    ref_args+=(--cases-dir "evals/test_cases" --qa-file "evals/simple_qa.jsonl")
  else
    echo "ERROR: unknown mode '${mode}' for ${runs_dir}" >&2
    exit 2
  fi

  echo
  echo "==> Scoring ${runs_dir} (mode=${mode})"
  echo "    judge_id=${judge_id}"

  python3 evals/score_runs.py \
    --config "${SCORING_CONFIG_PATH}" \
    --runs-dir "${runs_dir}" \
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

  echo "    wrote judgments: ${judgments_out}"
  echo "    wrote summary:   ${summary_out}"
}

print_budget
target_total=${#TARGETS[@]}
target_index=0
for target in "${TARGETS[@]}"; do
  target_index=$((target_index + 1))
  IFS="|" read -r runs_dir mode <<< "${target}"
  score_target "${runs_dir}" "${mode}" "${target_index}" "${target_total}"
  print_budget
done

echo
echo "Done: paper-scope rescoring complete."
