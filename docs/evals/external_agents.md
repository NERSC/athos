# Evaluating External Coding Agents

ATHOS evals can compare ATHOS flows against standalone coding agents. Two
wrappers run Claude Code and Codex headlessly on the same cases and write
JSONL that the normal import, scoring and summary tools understand:

- `scripts/run_claude_code_eval.py`
- `scripts/run_codex_eval.py`

For the run, judgment and directory formats see
[`eval_pipeline_v2.md`](../eval_pipeline_v2.md).

## Workflow

```text
run_claude_code_eval.py / run_codex_eval.py   -> external_runs.jsonl
evals/import_runs.py                          -> results/<experiment>/.../run.json
evals/score_runs.py                           -> judgments JSONL
evals/summarize_results.py                    -> aggregates/summary.json
```

The wrappers run outside ATHOS and call the `claude` or `codex` CLI, which must
be installed and authenticated. Each case is one CLI invocation.

## Inputs

- `--qa-file` (default `evals/simple_qa.jsonl`) and `--cases-dir` (default
  `evals/test_cases`) select the cases, in the same formats the ATHOS runner
  uses.
- `--bundle-root` (default `workspace/file_retrieval_corpus`) is a directory of
  reference files the agent may read. **It must contain an `INDEX.md`**; the
  scripts stop if it is missing, including for `--dry-run`. The prompt tells the
  agent to treat the bundle as its main evidence source and to read `INDEX.md`
  first. Build one with `scripts/build_workspace.py` (for example
  `--fs-docs-dir <docs> --build-fs-index --workspace-dir <workspace>`), or
  create the directory and index by hand.
- `--case-id` (repeatable) limits the run to specific cases.

The prompt gives the agent the case input (for directory cases, the user
description plus the attached files), tells it not to read `solution.md` and not
to modify files, and asks for a JSON answer with `answer`, `citations` and
optional `notes`.

## Running

```bash
# List the selected cases without invoking the agent
python scripts/run_claude_code_eval.py --bundle-root <bundle> --dry-run

# Smoke test on two cases
python scripts/run_claude_code_eval.py \
  --bundle-root <bundle> \
  --case-id perlmutter_debug_qos --case-id sbatch-qos-error \
  --output results/external_runs/claude_code_smoke.jsonl

# Full small set
python scripts/run_codex_eval.py \
  --bundle-root <bundle> \
  --output results/external_runs/codex_run1.jsonl
```

Notes:

- The scripts **append** to `--output`. Use a new file name per attempt, or
  delete the old file, so failed smoke records do not mix with full runs.
- Each invocation runs in a fresh temporary working directory; only the bundle
  is added as an extra readable path.
- Claude Code: `--permission-mode` defaults to `default`. Do not use
  `bypassPermissions` unless you intend to. `--disallowed-tools` takes a
  comma-separated list of built-in tools to deny; by default none are denied.
- Codex: `--sandbox-mode` defaults to `workspace-write`; `--enable-web-search`
  turns on web search, which is off by default.
- `--agent-system`, `--agent-version`, `--config-id` and `--config-ref` label the
  records. Keep `config_id` stable across repeats of the same setup, and change
  it when you change the model, tools or prompt. `config_ref` is free text that
  points at whatever documents the setup (default: the script path).

## Output records

One JSON object per case attempt:

```json
{
  "run_id": "uuid",
  "dataset_id": "test_cases",
  "case_id": "sbatch-qos-error",
  "run_index": 0,
  "agent_system": "claude_code",
  "agent_version": "claude-sonnet",
  "config_id": "claude_code_fs_bundle_v1",
  "config_ref": "scripts/run_claude_code_eval.py",
  "request": {"input_text": "full prompt sent to the agent"},
  "response": {"output_text": "final answer"},
  "execution": {
    "status": "success",
    "started_at_utc": "2026-01-01T00:00:00Z",
    "finished_at_utc": "2026-01-01T00:00:18Z",
    "error_type": null,
    "error_message": null
  },
  "metrics": {
    "latency_ms": 18000,
    "token_usage": {"input_tokens": 12345, "output_tokens": 456, "total_tokens": 13801}
  },
  "provenance": {"runner": "scripts/run_claude_code_eval.py", "command": "...", "hostname": "..."}
}
```

- `dataset_id` is the name of the dataset file or directory (`simple_qa` for
  `evals/simple_qa.jsonl`, `test_cases` for `evals/test_cases`). `score_runs.py`
  looks up references by `(dataset_id, case_id)`, so these must match the
  `--qa-file` / `--cases-dir` names you give the scorer.
- Claude Code metrics come from the CLI's own JSON result: reported duration
  (`latency_ms`), API duration (`latency_api_ms`), `cost_usd`, and input, output
  and cache token counts. Codex reports token usage in its event stream;
  `latency_ms` is measured by the wrapper around the call.
- Claude Code records also keep the session id, per-model usage, permission
  denials and the raw stdout under `provenance`.

### Failures

Failed attempts are still written, with `execution.status` set to
`execution_error`, `response.output_text` null, and `error_type` set to one of:

| `error_type` | Meaning |
| --- | --- |
| `CliError` | Claude Code exited non-zero. |
| `JsonParseError` | Claude Code output was not valid JSON. |
| `ClaudeResultError` | Claude Code exited cleanly but its result was not a success. |
| `CodexExecError` | `codex exec` failed. |

Raw stdout and stderr are kept under `provenance` for debugging. The importer
requires non-success records to carry `error_type` or `error_message`.

## Import, score and summarize

```bash
python evals/import_runs.py \
  --input results/external_runs/claude_code_run1.jsonl \
  --output-dir results \
  --experiment-id external_example

python evals/score_runs.py \
  --runs-dir results/external_example \
  --judge-model <judge> \
  --output results/external_example/judgments/<judge_id>.jsonl

python evals/summarize_results.py \
  --runs-dir results/external_example \
  --judgments-dir results/external_example/judgments \
  --output results/external_example/aggregates/summary.json
```

Check `evals/README.md` for the full set of scorer and summary options.
