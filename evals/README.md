# ATHOS evaluations

This directory contains test cases and utilities for evaluating ATHOS agent flows on common HPC troubleshooting scenarios as well as simple question/answer prompts.

## JSONL question/answer format

Q&A datasets are supplied as [JSON Lines](https://jsonlines.org/) files where each line is a standalone JSON object with three keys: `name`, `question`, and `answer`.

Example:

```jsonl
{"name": "perlmutter_gpus", "question": "What type of GPUs are in the Perlmutter supercomputer?", "answer": "Nvidia A100s, 40G and 80G types"}
```

Pass one or more of these files to `run_evaluations.py` using the `--qa-file` flag.

## Usage

```bash
# Ensure required environment variables for your LLM models are set (e.g., CBORG_API_KEY, CBORG_API_URL).
python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow <flow_name> [<flow_name2> ...] \
  [--cases-dir <dir1> --cases-dir <dir2> ...] \
  [--qa-file <qa.jsonl> ...] \
  [--output-dir <results_root>] \
  [--experiment-id <experiment_id>] \
  [--agent-system <agent_system>] \
  [--run-count <N>] \
  [--run-start <K>] \
  [--allow-overwrite-runs] \
  [--output results.json]
```

Arguments:
- `--config`: Path to the ATHOS YAML config file (default: `config/config.yaml`).
- `--flow`: One or more flow names to test (required).
- `--cases-dir`: Directory containing structured test case subdirectories. May be provided multiple times. Defaults to `test_cases` if no datasets are specified.
- `--qa-file`: JSONL file of question/answer pairs. May be provided multiple times.
- `--output-dir`: Root directory for canonical per-run output (`run.json` files).
- `--experiment-id`: Required when `--output-dir` is set. Used in canonical output paths.
- `--agent-system`: Agent system label for canonical output (default: `athos`).
- `--run-count`: Number of repeated runs per case (default: `1`).
- `--run-start`: Starting run index (default: `0`).
- `--allow-overwrite-runs`: Permit overwriting an existing canonical `run.json`.
- `--output`: File path to write a JSON report of results.

Notes:
- `--output` and `--output-dir` can be used together (legacy summary + canonical per-run records).
- `--experiment-id` is required if `--output-dir` is provided.
- Canonical run paths are immutable by default; duplicate run paths fail unless `--allow-overwrite-runs` is used.

## Canonical per-run output

When `--output-dir` is set, each attempt is written to:

`<output-dir>/<experiment_id>/<agent_system>/<config_id>/<case_id>/<run_index>/run.json`

Example:

`results/cug2026_main/athos/lang_chat__cborg_coder__abc12345/sbatch-qos-error/0/run.json`

### Running specific datasets

- **HPC troubleshooting cases only** (default):
  ```bash
  python evals/run_evaluations.py --config config/config.yaml --flow lang_chat
  ```
- **Q&A cases only**:
  ```bash
  python evals/run_evaluations.py --config config/config.yaml --flow lang_chat --qa-file evals/simple_qa.jsonl
  ```
- **Both HPC and Q&A cases**:
  ```bash
  python evals/run_evaluations.py --config config/config.yaml --flow lang_chat --cases-dir evals/test_cases --qa-file evals/simple_qa.jsonl
  ```

### Run-first examples

- **Generate canonical run records (single run index):**
  ```bash
  python evals/run_evaluations.py \
    --config config/config.yaml \
    --flow lang_chat \
    --cases-dir evals/test_cases \
    --output-dir results \
    --experiment-id cug2026_main
  ```

- **Append additional attempts later (run indices 3,4,5):**
  ```bash
  python evals/run_evaluations.py \
    --config config/config.yaml \
    --flow lang_chat \
    --cases-dir evals/test_cases \
    --output-dir results \
    --experiment-id cug2026_main \
    --run-start 3 \
    --run-count 3
  ```

- **Execution-only runs (default behavior):**
  ```bash
  python evals/run_evaluations.py \
    --config config/config.yaml \
    --flow lang_chat \
    --cases-dir evals/test_cases \
    --output-dir results \
    --experiment-id cug2026_main
  ```

## Scoring canonical runs

Use `evals/score_runs.py` to score canonical `run.json` files and write
append-only judgments JSONL (`athos.judgment.v1`).

```bash
python evals/score_runs.py \
  --config config/config.yaml \
  --runs-dir results/cug2026_main \
  --cases-dir evals/test_cases \
  --judge-model cborg_chat \
  --judge-id cborg_chat_rubric_v2 \
  --judge-prompt-version rubric_v2 \
  --fail-on-skip \
  --skips-output results/cug2026_main/judgments/cborg_chat_rubric_v2.skips.jsonl \
  --output results/cug2026_main/judgments/cborg_chat_rubric_v2.jsonl
```

Arguments:
- `--runs-dir`: Directory tree to scan for `run.json` files.
- `--runs-manifest`: Optional manifest file listing run paths (one per line, or JSONL with `{"path": ...}`).
- `--judge-model`: Model name from config used for judging (required).
- `--judge-id`: Logical judge identifier (defaults to `<judge-model>:<judge-prompt-version>`).
- `--judge-prompt-version`: Prompt version label for traceability (default: `v1`).
- `--cases-dir` / `--qa-file`: Reference datasets used to resolve expected answers by `case_id`.
- `--fail-on-skip`: Exit non-zero if any run cannot be scored.
- `--skips-output`: Optional JSONL path for detailed skip records.
- `--output`: Judgments JSONL output path (append mode).

Judgment status:
- Scored judgments use `judgment_status: "scored"` with numeric `score` and boolean `pass`.
- Unscorable judgments are still written with `judgment_status` like:
  - `skipped_missing_reference`
  - `skipped_missing_output`
  - `skipped_invalid_run`
  In those cases `score` and `pass` are `null`.

## Import external runs

Use `evals/import_runs.py` to normalize external outputs into canonical run records.

```bash
python evals/import_runs.py \
  --input external_runs.jsonl \
  --output-dir results \
  --experiment-id cug2026_main \
  --dataset-id hpc_troubleshooting_v1
```

Required fields per record:
- `case_id`
- `agent_system`
- `config_id`
- Either `response.output_text` (or top-level `output_text`) for success, or non-success execution with error details.

## Summarize runs and judgments

Use `evals/summarize_results.py` to produce grouped aggregates.

```bash
python evals/summarize_results.py \
  --runs-dir results/cug2026_main \
  --judgments-dir results/cug2026_main/judgments \
  --output results/cug2026_main/aggregates/summary.json
```

Summary aggregates include `run_count`, `scored_count`, `skipped_count`,
`skipped_by_reason`, and score/pass metrics computed from scored judgments only.

## Available test cases

Current examples included in this repo:
- `hf-home-hang`
- `pytorch-launch-error`
- `pytorch-launch-error-2`
- `sbatch-qos-error`
- `vasp-license-error`
- `salloc-account-error`
- `gpu-misconfiguration`
