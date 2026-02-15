# ATHOS Eval Pipeline v2: Run-First Schema

This document defines a scalable evaluation workflow for ATHOS and external agents.

## Goals
- Support many configs, repeated runs, and asynchronous execution over time.
- Keep raw execution outputs immutable and auditable.
- Decouple execution from judging/scoring.
- Allow non-ATHOS systems (e.g., Codex, human baselines) to submit compatible outputs.

## Storage Model

Canonical storage is **one file per run attempt**.

Directory contract:

`results/<experiment_id>/<agent_system>/<config_id>/<case_id>/<run_index>/run.json`

Where:
- `experiment_id`: campaign grouping (e.g., `cug2026_main`).
- `agent_system`: `athos`, `codex`, `human`, etc.
- `config_id`: deterministic ID for model/flow/prompt/tooling config.
- `case_id`: stable test case identifier.
- `run_index`: integer run index (`0`, `1`, ...).

Derived artifacts (optional):
- `results/<experiment_id>/manifests/runs.jsonl` (append-only run index)
- `results/<experiment_id>/judgments/<judge_id>.jsonl`
- `results/<experiment_id>/aggregates/*.json` or `*.parquet`

## Case Dataset Contract

Cases should have stable IDs and versioning:

```json
{
  "dataset_id": "hpc_troubleshooting_v1",
  "dataset_version": "2026-02-14",
  "case_id": "sbatch-qos-error",
  "input": "...user prompt or assembled scenario...",
  "reference": "...reference solution...",
  "tags": ["slurm", "qos", "user-support"]
}
```

## `run.json` Schema (Canonical)

```json
{
  "schema_version": "athos.run.v1",
  "run_id": "uuid",
  "experiment_id": "cug2026_main",
  "dataset_id": "hpc_troubleshooting_v1",
  "dataset_version": "2026-02-14",
  "case_id": "sbatch-qos-error",
  "run_index": 0,
  "agent_system": "athos",
  "agent_version": "git:cef7f764a02b9ef0b6f8bd3bfa8fde82c1a15ffd",
  "config_id": "lang_chat__cborg_coder__abc12345",
  "config_ref": "config/paper/lang_chat_baseline.yaml",
  "execution": {
    "started_at_utc": "2026-02-14T12:00:00Z",
    "finished_at_utc": "2026-02-14T12:00:13Z",
    "status": "success",
    "error_type": null,
    "error_message": null
  },
  "request": {
    "input_text": "...",
    "input_artifacts": []
  },
  "response": {
    "output_text": "...",
    "output_artifacts": []
  },
  "metrics": {
    "latency_ms": 13123.4,
    "token_usage": {
      "input_tokens": 301,
      "output_tokens": 928
    },
    "tool_calls": []
  },
  "provenance": {
    "runner": "athos-eval generate",
    "command": "athos-eval generate ...",
    "hostname": "perlmutter",
    "git_sha": "cef7f764a02b9ef0b6f8bd3bfa8fde82c1a15ffd",
    "env_fingerprint": "sha256:..."
  }
}
```

Notes:
- `status` values: `success`, `execution_error`, `timeout`, `invalid_output`.
- `output_text` must be present for `success`; otherwise `null` is allowed.
- External submitters may omit unavailable metrics, but must include required IDs and `output_text` or error fields.

## Judgment Schema (Decoupled)

Store scoring separately so runs can be re-judged later.

```json
{
  "schema_version": "athos.judgment.v1",
  "score_id": "uuid",
  "run_id": "uuid",
  "judge_id": "cborg_chat_rubric_v2",
  "judge_model": "lbl/cborg-chat:latest",
  "judge_prompt_version": "rubric_v2",
  "scored_at_utc": "2026-02-14T13:00:00Z",
  "score": 84.0,
  "pass": true,
  "rationale": "...",
  "subscores": {
    "correctness": 4,
    "actionability": 5
  }
}
```

## Minimal Workflow

1. Generate runs:
   - Execute cases and write one `run.json` per attempt.
2. Score runs:
   - Read run files, apply judge(s), write judgments JSONL.
3. Aggregate:
   - Join runs + judgments, compute means/variance/CI by grouping keys.

Recommended grouping keys:
- `experiment_id`
- `agent_system`
- `config_id`
- `dataset_id`
- `case_id`

## Deterministic IDs

- `config_id`: hash normalized config subset used for execution (model/flow/tools/prompts).
- `run_id`: UUIDv4.
- `score_id`: UUIDv4.

## Migration Plan from Current Script

1. Add `--output-dir` mode in `evals/run_evaluations.py` to emit per-run files.
2. Add a scorer command that reads run files and writes judgments.
3. Keep current summary JSON as a derived report for backwards compatibility.

## Implementation Plan (Detailed)

### Phase 1: Dual-Write Execution Output

Extend `evals/run_evaluations.py` with:
- `--experiment-id <str>`: required when `--output-dir` is set.
- `--agent-system <str>`: default `athos`.
- `--output-dir <path>`: enables canonical per-run writes.
- `--run-count <int>`: default `1`; emits `run_index = K..K+N-1`.
- `--run-start <int>`: default `0`; starting `run_index`.
- `--no-score`: execute only, skip judging.

Behavior:
- Legacy `--output` summary remains unchanged.
- When `--output-dir` is set, write one `run.json` for each `(flow, dataset, case, run_index)`.

Acceptance checks:
- Existing integration tests for `evals/run_evaluations.py` still pass.
- A single run with both `--output` and `--output-dir` produces both artifacts.
- Re-running later with higher `--run-start` writes new run directories without mutating prior `run.json`.

### Phase 2: Separate Scoring Command

Add `evals/score_runs.py`:
- Input: run files discovered under `--runs-dir` or listed via `--runs-manifest`.
- Options: `--judge-model`, `--judge-prompt-version`, `--judge-id`, `--output`.
- Output: append-only judgments JSONL (`athos.judgment.v1`).

Acceptance checks:
- Scoring succeeds against both ATHOS-generated and imported run files.
- Re-scoring identical runs with a different judge prompt/model produces a separate judgments file.
- Judge metadata (`judge_id`, `judge_prompt_version`) is always populated.

### Phase 3: External Run Import

Add `evals/import_runs.py`:
- Input: JSONL/JSON with external system outputs.
- Required fields: `case_id`, `agent_system`, `config_id`, and either `response.output_text` or non-success status.
- Output: normalized canonical `run.json` files under v2 directory layout.

Acceptance checks:
- Invalid records are rejected with explicit validation errors.
- Valid external records score correctly with `score_runs.py`.

### Phase 4: Derived Summaries

Add `evals/summarize_results.py`:
- Join canonical runs and judgments.
- Emit aggregate tables by `experiment_id`, `agent_system`, `config_id`, `dataset_id`.
- Include variance metrics (`mean`, `stddev`, and confidence interval where sample count permits).

Acceptance checks:
- Summary values match direct recomputation from raw records.
- For legacy-compatible runs, aggregate score/pass outputs match current script within tolerance.

## Legacy Deprecation Criteria

Keep legacy monolithic summary mode until all conditions are met:
- Canonical per-run output is enabled in default evaluation jobs.
- Separate scoring command is used in paper pipelines.
- Summary generation is validated as fully derived from run/judgment records.
- At least one full experiment is completed with multiple run indices and regenerated summaries.

After these are satisfied, mark legacy inline-scoring summary mode as deprecated in docs, but keep it available for one release window.
