#!/usr/bin/env bash

set -euo pipefail

# Score + summarize an imported external-run experiment (e.g., Codex/Claude).
#
# Usage examples:
#   EXPERIMENT_ID=cug_codex_external_mini_20260313_232712 scripts/score_cug_external.sh
#   RUNS_DIR=results/cug_codex_external_mini_20260313_232712 scripts/score_cug_external.sh
#   EXTERNAL_RUNS_INPUT=results/external_runs/claude_code_fs_bundle_v1_mini_20260314.success_only.jsonl \
#     EXPERIMENT_ID=cug_claude_external_mini_20260314 \
#     scripts/score_cug_external.sh

SCORING_CONFIG_PATH="${SCORING_CONFIG_PATH:-config/paper/cug_m1.yaml}"
RESULTS_ROOT="${RESULTS_ROOT:-results}"
RUNS_DIR="${RUNS_DIR:-}"
EXPERIMENT_ID="${EXPERIMENT_ID:-}"
EXTERNAL_RUNS_INPUT="${EXTERNAL_RUNS_INPUT:-}"
IMPORT_ALLOW_OVERWRITE="${IMPORT_ALLOW_OVERWRITE:-1}"
NORMALIZE_EXTERNAL_RUNS="${NORMALIZE_EXTERNAL_RUNS:-1}"

JUDGE_MODEL="${JUDGE_MODEL:-llama_4_maverick}"
JUDGE_PROMPT_VERSION="${JUDGE_PROMPT_VERSION:-rubric_v1}"
JUDGE_ID="${JUDGE_ID:-${JUDGE_MODEL}_${JUDGE_PROMPT_VERSION}}"
PASSING_SCORE="${PASSING_SCORE:-80}"
JUDGE_MAX_ATTEMPTS="${JUDGE_MAX_ATTEMPTS:-5}"
JUDGE_RETRY_DELAY_MS="${JUDGE_RETRY_DELAY_MS:-1500}"

# Keep default non-fatal so summaries still materialize on transient judge errors.
FAIL_ON_SKIP="${FAIL_ON_SKIP:-0}"

CASES_DIRS="${CASES_DIRS:-evals/test_cases}"
QA_FILES="${QA_FILES:-evals/simple_qa.jsonl}"
STRICT_DATASET_PATHS="${STRICT_DATASET_PATHS:-1}"

start_epoch="$(date +%s)"
start_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ -n "${EXTERNAL_RUNS_INPUT}" ]]; then
  if [[ -z "${EXPERIMENT_ID}" ]]; then
    echo "ERROR: EXTERNAL_RUNS_INPUT requires EXPERIMENT_ID" >&2
    exit 2
  fi
  if [[ ! -f "${EXTERNAL_RUNS_INPUT}" ]]; then
    echo "ERROR: external runs input not found: ${EXTERNAL_RUNS_INPUT}" >&2
    exit 2
  fi
  if [[ -z "${RUNS_DIR}" ]]; then
    RUNS_DIR="${RESULTS_ROOT}/${EXPERIMENT_ID}"
  fi
  import_input="${EXTERNAL_RUNS_INPUT}"
  normalized_input_tmp=""
  if [[ "${NORMALIZE_EXTERNAL_RUNS}" == "1" ]]; then
    tmp_root="${TMPDIR:-/tmp}"
    normalized_input_tmp="$(mktemp "${tmp_root%/}/external_runs_normalized.XXXXXX")"
    normalized_input_tmp="${normalized_input_tmp}.jsonl"
    python3 - "${EXTERNAL_RUNS_INPUT}" "${normalized_input_tmp}" <<'PY'
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])

fixed = 0
rows = 0
with src.open("r", encoding="utf-8") as rf, dst.open("w", encoding="utf-8") as wf:
    for line in rf:
        text = line.strip()
        if not text:
            continue
        rows += 1
        rec = json.loads(text)
        status = ((rec.get("execution") or {}).get("status"))
        response = rec.get("response")
        output_text = (response or {}).get("output_text") if isinstance(response, dict) else None
        if status == "success" and (not isinstance(output_text, str) or not output_text.strip()):
            raw_stdout = ((rec.get("provenance") or {}).get("raw_stdout"))
            candidate = None
            if isinstance(raw_stdout, str) and raw_stdout.strip():
                try:
                    payload = json.loads(raw_stdout)
                except json.JSONDecodeError:
                    payload = {}
                if isinstance(payload, dict):
                    structured = payload.get("structured_output")
                    if isinstance(structured, dict):
                        ans = structured.get("answer")
                        if isinstance(ans, str) and ans.strip():
                            candidate = ans.strip()
                    if candidate is None:
                        res = payload.get("result")
                        if isinstance(res, str) and res.strip():
                            candidate = res.strip()
            if candidate:
                if not isinstance(response, dict):
                    rec["response"] = {}
                    response = rec["response"]
                response["output_text"] = candidate
                fixed += 1
        wf.write(json.dumps(rec) + "\n")

print(f"normalized_rows={rows} fixed_missing_output_text={fixed}")
PY
    import_input="${normalized_input_tmp}"
  fi

  import_cmd=(
    python evals/import_runs.py
    --input "${import_input}"
    --output-dir "${RESULTS_ROOT}"
    --experiment-id "${EXPERIMENT_ID}"
  )
  if [[ "${IMPORT_ALLOW_OVERWRITE}" == "1" ]]; then
    import_cmd+=(--allow-overwrite-runs)
  fi
  echo "Importing external runs"
  echo "  input: ${EXTERNAL_RUNS_INPUT}"
  if [[ -n "${normalized_input_tmp}" ]]; then
    echo "  normalized_input: ${normalized_input_tmp}"
  fi
  echo "  output_dir: ${RESULTS_ROOT}"
  echo "  experiment_id: ${EXPERIMENT_ID}"
  echo "  allow_overwrite: ${IMPORT_ALLOW_OVERWRITE}"
  "${import_cmd[@]}"
  if [[ -n "${normalized_input_tmp}" ]]; then
    rm -f "${normalized_input_tmp}"
  fi
fi

if [[ -z "${RUNS_DIR}" ]]; then
  if [[ -z "${EXPERIMENT_ID}" ]]; then
    echo "ERROR: set RUNS_DIR or EXPERIMENT_ID (or EXTERNAL_RUNS_INPUT+EXPERIMENT_ID)" >&2
    exit 2
  fi
  RUNS_DIR="${RESULTS_ROOT}/${EXPERIMENT_ID}"
fi

if [[ ! -d "${RUNS_DIR}" ]]; then
  echo "ERROR: runs directory not found: ${RUNS_DIR}" >&2
  exit 2
fi

read -r -a cases_args <<< "${CASES_DIRS}"
resolved_cases=()
missing_cases=()
for cases_dir in "${cases_args[@]}"; do
  [[ -z "${cases_dir}" ]] && continue
  if [[ -d "${cases_dir}" ]]; then
    resolved_cases+=("${cases_dir}")
  else
    missing_cases+=("${cases_dir}")
  fi
done

read -r -a qa_args <<< "${QA_FILES}"
resolved_qa=()
missing_qa=()
for qa_file in "${qa_args[@]}"; do
  [[ -z "${qa_file}" ]] && continue
  if [[ -f "${qa_file}" ]]; then
    resolved_qa+=("${qa_file}")
  else
    missing_qa+=("${qa_file}")
  fi
done

if [[ ${#resolved_cases[@]} -eq 0 && ${#resolved_qa[@]} -eq 0 ]]; then
  echo "ERROR: no valid reference datasets found from CASES_DIRS/QA_FILES." >&2
  exit 2
fi

if [[ "${STRICT_DATASET_PATHS}" == "1" && ( ${#missing_cases[@]} -gt 0 || ${#missing_qa[@]} -gt 0 ) ]]; then
  echo "ERROR: missing dataset paths under STRICT_DATASET_PATHS=1" >&2
  for item in "${missing_cases[@]}"; do
    echo "  missing cases-dir: ${item}" >&2
  done
  for item in "${missing_qa[@]}"; do
    echo "  missing qa-file: ${item}" >&2
  done
  exit 2
fi

JUDGMENTS_DIR="${JUDGMENTS_DIR:-${RUNS_DIR}/judgments}"
AGGREGATES_DIR="${AGGREGATES_DIR:-${RUNS_DIR}/aggregates}"
JUDGMENTS_OUT="${JUDGMENTS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.jsonl}"
SKIPS_OUT="${SKIPS_OUT:-${JUDGMENTS_DIR}/${JUDGE_ID}.skips.jsonl}"
SUMMARY_OUT="${SUMMARY_OUT:-${AGGREGATES_DIR}/summary.json}"

mkdir -p "${JUDGMENTS_DIR}" "${AGGREGATES_DIR}"

score_cmd=(
  python evals/score_runs.py
  --config "${SCORING_CONFIG_PATH}"
  --runs-dir "${RUNS_DIR}"
  --judge-model "${JUDGE_MODEL}"
  --judge-id "${JUDGE_ID}"
  --judge-prompt-version "${JUDGE_PROMPT_VERSION}"
  --judge-max-attempts "${JUDGE_MAX_ATTEMPTS}"
  --judge-retry-delay-ms "${JUDGE_RETRY_DELAY_MS}"
  --passing-score "${PASSING_SCORE}"
  --skips-output "${SKIPS_OUT}"
  --output "${JUDGMENTS_OUT}"
)

for cases_dir in "${resolved_cases[@]}"; do
  score_cmd+=(--cases-dir "${cases_dir}")
done

for qa_file in "${resolved_qa[@]}"; do
  score_cmd+=(--qa-file "${qa_file}")
done

if [[ "${FAIL_ON_SKIP}" == "1" ]]; then
  score_cmd+=(--fail-on-skip)
fi

echo "Scoring external CUG runs"
echo "  runs_dir: ${RUNS_DIR}"
echo "  config: ${SCORING_CONFIG_PATH}"
echo "  judge_model: ${JUDGE_MODEL}"
echo "  judge_id: ${JUDGE_ID}"
echo "  judge_max_attempts: ${JUDGE_MAX_ATTEMPTS}"
echo "  judge_retry_delay_ms: ${JUDGE_RETRY_DELAY_MS}"
echo "  fail_on_skip: ${FAIL_ON_SKIP}"
echo "  strict_dataset_paths: ${STRICT_DATASET_PATHS}"
echo "  judgments_out: ${JUDGMENTS_OUT}"
echo "  skips_out: ${SKIPS_OUT}"
echo "  started_at_utc: ${start_utc}"

if [[ ${#resolved_cases[@]} -gt 0 ]]; then
  echo "  cases_dirs: ${resolved_cases[*]}"
fi
if [[ ${#resolved_qa[@]} -gt 0 ]]; then
  echo "  qa_files: ${resolved_qa[*]}"
fi
if [[ ${#missing_cases[@]} -gt 0 ]]; then
  echo "  warning_missing_cases_dirs: ${missing_cases[*]}"
fi
if [[ ${#missing_qa[@]} -gt 0 ]]; then
  echo "  warning_missing_qa_files: ${missing_qa[*]}"
fi

"${score_cmd[@]}"

echo "Summarizing runs + judgments"
echo "  summary_out: ${SUMMARY_OUT}"

python evals/summarize_results.py \
  --runs-dir "${RUNS_DIR}" \
  --judgment-file "${JUDGMENTS_OUT}" \
  --output "${SUMMARY_OUT}"

end_epoch="$(date +%s)"
end_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
elapsed_sec="$((end_epoch - start_epoch))"

echo "Done."
echo "  Judgments: ${JUDGMENTS_OUT}"
echo "  Skips: ${SKIPS_OUT}"
echo "  Summary: ${SUMMARY_OUT}"
echo "Run timing summary:"
echo "  started_at_utc: ${start_utc}"
echo "  finished_at_utc: ${end_utc}"
echo "  elapsed_seconds: ${elapsed_sec}"
