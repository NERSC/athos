# ATHOS Eval Pipeline v2: Run-First Schema

This document defines a scalable evaluation workflow for ATHOS and external agents.

## Goals
- Support many configs, repeated runs, and asynchronous execution over time.
- Keep raw execution outputs immutable and auditable.
- Decouple execution from judging/scoring.
- Allow non-ATHOS systems (e.g., Codex, Claude Code, human baselines) to submit compatible outputs.

## Storage Model

Canonical storage is **one file per run attempt**.

Directory contract:

`results/<experiment_id>/<agent_system>/<config_id>/<dataset_id>/<case_id>/<run_index>/run.json`

Where:
- `experiment_id`: campaign grouping (e.g., `my_experiment`).
- `agent_system`: `athos`, `codex`, `human`, etc.
- `config_id`: deterministic ID for model/flow/prompt/tooling config.
- `dataset_id`: source dataset namespace (e.g., `test_cases`, `simple_qa`).
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
  "experiment_id": "my_experiment",
  "dataset_id": "hpc_troubleshooting_v1",
  "dataset_version": "2026-02-14",
  "case_id": "sbatch-qos-error",
  "run_index": 0,
  "agent_system": "athos",
  "agent_version": "git:cef7f764a02b9ef0b6f8bd3bfa8fde82c1a15ffd",
  "config_id": "lang_chat__cborg_coder__abc12345",
  "config_ref": "config/config.yaml",
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
    "runner": "evals/run_evaluations.py",
    "command": "python evals/run_evaluations.py ...",
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

## Tools

| Step | Tool | Notes |
| --- | --- | --- |
| Generate runs | `evals/run_evaluations.py` | Writes one immutable `run.json` per attempt; use `--run-count` / `--run-start` for repeats. |
| Import external runs | `evals/import_runs.py` | Normalizes JSONL/JSON from other systems into the same layout. Required: `case_id`, `agent_system`, `config_id`, and either `response.output_text` or a non-success status. Invalid records are rejected with explicit errors. |
| Score runs | `evals/score_runs.py` | Reads run files (`--runs-dir` or `--runs-manifest`) and appends judgments (`athos.judgment.v1`). Re-scoring with another judge writes a separate file. |
| Summarize | `evals/summarize_results.py` | Joins runs and judgments; aggregates by experiment, agent system, config and dataset, with variance metrics. |

Wrapper scripts: `scripts/run_evals.sh` (execution only),
`scripts/run_test_evals.sh` (end-to-end smoke test) and `scripts/run_cug_eval.sh`
(run, score and summarize with the CUG paper profiles).
`scripts/run_claude_code_eval.py` and `scripts/run_codex_eval.py` run external
coding agents on the same cases and emit JSONL for `evals/import_runs.py`.

Runs are never modified after being written. Inline scoring in
`evals/run_evaluations.py` has been removed; scoring happens only through
`evals/score_runs.py`.
