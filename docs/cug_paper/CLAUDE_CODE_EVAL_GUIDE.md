# Claude Code External Eval Guide

This guide describes how to run a standalone coding agent on the ATHOS paper evals and produce raw external-run JSONL for later import into the ATHOS scoring pipeline.

Current recommendation:
- prioritize the focused small comparison first
- use the same M1 small datasets already used in the paper's harness comparison

This is an external baseline path. The agent runs outside ATHOS, and its outputs are captured as raw external-run records for later import by the ATHOS maintainer.

## Scope

Recommended first study:
- dataset slice: `evals/simple_qa.jsonl` + `evals/test_cases`
- effective size: 5 Q&A cases + 7 ticket-style cases
- run policy: `run_count=1`
- agent system label: `claude_code`
- config lineage label: `claude_code_fs_bundle_v1`

Only move on to the expanded datasets after the focused run is stable and produces machine-ingestable outputs.

## Required Inputs

Collaborators should use the ATHOS repo checkout for:
- `scripts/run_claude_code_eval.py`
- `evals/simple_qa.jsonl`
- `evals/test_cases`

You provide only the file corpus bundle:
- `<path/to/file_retrieval_corpus>`

If `<path/to/file_retrieval_corpus>/INDEX.md` is missing, stop before running.

## Recommended Execution Model

Use one Claude Code process per benchmark case.

For each case:
1. build a single prompt containing the user-visible case input
2. instruct Claude Code to use the provided bundle `INDEX.md` first
3. request structured JSON output only
4. record wall-clock start and finish timestamps outside the CLI
5. parse the Claude Code result JSON
6. append one JSON record to an external-runs JSONL file

After all cases complete:
1. check that the external-runs JSONL looks complete
2. share that JSONL back with the ATHOS maintainer

The maintainer can then import, score, and summarize the runs centrally.

## Output Contract

The wrapper should write one JSON object per attempt to a JSONL file. Use this schema:

```json
{
  "run_id": "optional-uuid",
  "case_id": "sbatch-qos-error",
  "dataset_id": "test_cases",
  "run_index": 0,
  "agent_system": "claude_code",
  "agent_version": "claude-sonnet-4.5",
  "config_id": "claude_code_fs_bundle_v1",
  "config_ref": "docs/cug_paper/CLAUDE_CODE_EVAL_GUIDE.md",
  "request": {
    "input_text": "full prompt sent to Claude Code"
  },
  "response": {
    "output_text": "final answer text"
  },
  "execution": {
    "status": "success",
    "started_at_utc": "2026-03-13T07:00:00Z",
    "finished_at_utc": "2026-03-13T07:00:18Z",
    "error_type": null,
    "error_message": null
  },
  "metrics": {
    "token_usage": {
      "input_tokens": 12345,
      "output_tokens": 456,
      "cache_creation_input_tokens": 1000,
      "cache_read_input_tokens": 0,
      "total_tokens": 13801
    },
    "latency_ms": 18000,
    "latency_api_ms": 16500,
    "cost_usd": 0.0635
  },
  "provenance": {
    "runner": "claude_code_wrapper",
    "command": "claude --print ...",
    "hostname": "login01",
    "git_sha": "optional",
    "session_id": "claude-session-id",
    "uuid": "cli-result-uuid",
    "model_usage": {}
  }
}
```

Notes:
- `dataset_id` must match ATHOS local dataset naming exactly:
  - `simple_qa` for `evals/simple_qa.jsonl`
  - `test_cases` for `evals/test_cases`
- Claude Code JSON output includes token usage, cost, and duration fields; prefer those values over offline estimation
- keep `metrics.latency_ms` aligned to Claude Code's reported `duration_ms`

## Prompting Rules

Use a consistent prompt across all cases.

Required prompt elements:
- identify the benchmark case id and dataset
- include the full case input exactly as presented to the user
- tell the agent not to inspect `solution.md`
- tell the agent to treat the provided file retrieval corpus as the main evidence source
- require reading the provided `INDEX.md` early
- require a concise final support answer
- require a JSON response with a fixed schema

Recommended behavioral rules:
- do not modify files
- keep shell/tool usage read-only
- prefer targeted reads over broad scans
- cite exact file paths when using bundle evidence
- stop once sufficient evidence is gathered

Recommended final-answer JSON schema:

```json
{
  "type": "object",
  "properties": {
    "answer": {"type": "string"},
    "citations": {
      "type": "array",
      "items": {"type": "string"}
    },
    "notes": {"type": "string"}
  },
  "required": ["answer", "citations"]
}
```

The wrapper can then place `answer` into `response.output_text` and keep `citations` and `notes` in sidecar logs if desired.

## Suggested Case Prompt Template

Use this prompt shape for each case:

```text
You are running a single ATHOS paper benchmark case as a standalone coding agent baseline.

Rules:
- Do not inspect any `solution.md` file.
- Do not modify repository files.
- Use read-only tool usage only.
- Treat `{bundle_root}` as your primary evidence source.
- Read `{bundle_root}/INDEX.md` before broader searching.
- Prefer targeted reads over repeated broad searches.
- Keep the final support answer concise and operationally useful.

Case metadata:
- dataset_id: {dataset_id}
- case_id: {case_id}

User-facing case input:
{case_input}

Return JSON only with this schema:
{
  "answer": "string",
  "citations": ["string"],
  "notes": "optional string"
}
```

For `test_cases`, `case_input` should include:
- `user_description.txt`
- all attached file contents from the case's `files/` directory

For `simple_qa`, `case_input` should just include the question text.

## Suggested Claude Code Invocation

The guide assumes a current Claude Code CLI with non-interactive print mode. A representative command shape is:

```bash
claude \
  --print \
  --output-format json \
  --permission-mode default \
  --json-schema '<SCHEMA_JSON>' \
  "<PROMPT>"
```

Operational notes:
- treat this as a trusted local repo only
- do not use `--dangerously-skip-permissions` for the collaborator workflow
- keep the run as read-only as your local Claude Code setup allows
- if your local Claude Code version does not support `--json-schema` cleanly, fall back to `--output-format text` and parse only the final JSON object from the answer body

Representative successful Claude Code result payload:

```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 1815,
  "duration_api_ms": 3083,
  "num_turns": 1,
  "result": "Hello! How can I help you with your project today?",
  "session_id": "ca0dd205-43d5-44bc-ac80-9621b6d69cfd",
  "total_cost_usd": 0.06354125000000001,
  "usage": {
    "input_tokens": 3,
    "cache_creation_input_tokens": 16719,
    "cache_read_input_tokens": 0,
    "output_tokens": 15
  },
  "modelUsage": {},
  "permission_denials": [],
  "uuid": "824b4e9e-1a3b-47ee-b9b6-dadc13f0e516"
}
```

The wrapper should treat this result object as the primary source of metrics.

## Metrics Capture

### Latency

Preferred approach:
- use Claude Code's reported `duration_ms` as `metrics.latency_ms`
- preserve `duration_api_ms` separately as `metrics.latency_api_ms`

Also record:
- `started_at_utc` immediately before invoking the CLI
- `finished_at_utc` immediately after it exits

The external timestamps are still useful for provenance and failure handling, but the paper-facing latency field should use Claude Code's own reported duration when present.

### Tokens

Use the token counts reported directly by Claude Code's JSON result:
- `usage.input_tokens`
- `usage.output_tokens`
- `usage.cache_creation_input_tokens`
- `usage.cache_read_input_tokens`

Compute:
- `metrics.token_usage.total_tokens` as the sum of those four fields

Also preserve:
- `total_cost_usd` as `metrics.cost_usd`
- `modelUsage` under provenance for later analysis of any multi-model routing behavior

Do not estimate tokens offline when Claude Code returns usage directly.

## Failure Handling

If Claude Code exits non-zero or produces invalid JSON:
- still write a JSONL record for that case
- set:
  - `execution.status` to `execution_error`
  - `execution.error_type` to a short classifier such as `CliError`, `JsonParseError`, or `Timeout`
  - `execution.error_message` to a short stderr summary
- leave `response.output_text` empty or null
- still record `started_at_utc` and `finished_at_utc`
- if Claude returned partial structured metrics before failure, preserve them

This lets ATHOS import and scoring preserve failure behavior rather than silently dropping cases.

## Suggested Wrapper Structure

Use the wrapper from the repo:

```bash
python scripts/run_claude_code_eval.py \
  --qa-file evals/simple_qa.jsonl \
  --cases-dir evals/test_cases \
  --bundle-root <path/to/file_retrieval_corpus> \
  --output results/external_runs/claude_code_fs_bundle_v1.jsonl
```

The wrapper:

1. enumerate all 5 Q&A cases from `evals/simple_qa.jsonl`
2. enumerate all 7 case directories under `evals/test_cases`
3. build one prompt per case
4. invoke Claude Code once per case
5. capture stdout, stderr, exit code, timestamps, and the Claude JSON result object
6. append one record per case to:
   - `results/external_runs/claude_code_fs_bundle_v1.jsonl`

By default, the wrapper leaves Claude tools unrestricted and runs Claude from an isolated temporary working directory with only the provided `--bundle-root` added as an allowed path.

Why a wrapper is preferred:
- easier JSON parsing
- cleaner latency capture
- cleaner failure handling
- direct compatibility with later import via `evals/import_runs.py`
- less opportunity for colleagues to accidentally drift from the agreed config lineage

Useful options:

```bash
python scripts/run_claude_code_eval.py \
  --qa-file evals/simple_qa.jsonl \
  --cases-dir evals/test_cases \
  --bundle-root <path/to/file_retrieval_corpus> \
  --dry-run

python scripts/run_claude_code_eval.py \
  --qa-file evals/simple_qa.jsonl \
  --cases-dir evals/test_cases \
  --bundle-root <path/to/file_retrieval_corpus> \
  --case-id perlmutter_debug_qos \
  --case-id sbatch-qos-error

python scripts/run_claude_code_eval.py \
  --qa-file evals/simple_qa.jsonl \
  --cases-dir evals/test_cases \
  --bundle-root <path/to/file_retrieval_corpus> \
  --model sonnet \
  --output results/external_runs/claude_code_fs_bundle_v1.jsonl
```

## Smoke Run

Before running all 12 cases, do a smoke run on:
- `simple_qa/perlmutter_debug_qos`
- `test_cases/sbatch-qos-error`

Example:

```bash
python scripts/run_claude_code_eval.py \
  --qa-file evals/simple_qa.jsonl \
  --cases-dir evals/test_cases \
  --bundle-root <path/to/file_retrieval_corpus> \
  --case-id perlmutter_debug_qos \
  --case-id sbatch-qos-error \
  --output results/external_runs/claude_code_fs_bundle_v1.smoke.jsonl
```

Success criteria:
- Claude Code returns valid structured output
- the wrapper writes valid JSONL records
- `dataset_id` values are exactly `simple_qa` and `test_cases`
- latency is captured
- the output JSONL is ready to share back for maintainer-side import and scoring

## What To Share Back

Assume the wrapper writes:

```bash
results/external_runs/claude_code_fs_bundle_v1.jsonl
```

Share the raw external JSONL file, not imported/scored ATHOS outputs.

What to send back:
- the JSONL file you wrote with `--output`

Optional helpful sidecars:
- a short note with the Claude Code version used
- any stderr logs for failed cases
- the exact command line if you changed wrapper defaults

The ATHOS maintainer can then handle:
- import
- scoring
- summarization
- paper-table assembly

## Known Caveats

1. This guide assumes Claude Code can be run headlessly in a trusted repo checkout.
2. Token reporting may vary by CLI version.
3. If the agent is allowed to roam the full repo, the comparison becomes less fair and less reproducible.
4. The first paper-facing priority is the focused 12-case comparison, not the full expanded-set sweep.

## Recommended Naming

Use these identifiers unless there is a clear reason to change them:
- `agent_system`: `claude_code`
- `config_id`: `claude_code_fs_bundle_v1`
- `experiment_id`: `cug_claude_code_small_<timestamp>`

This keeps the external baseline distinct from ATHOS-native `athos` runs while preserving a stable lineage for later repeats.
