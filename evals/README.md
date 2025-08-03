# ATHOS evaluations

This directory contains test cases and a script for evaluating ATHOS agent flows on common HPC troubleshooting scenarios.

Run the evaluation script to execute one or more flows on all test cases and grade the responses against the reference solutions.

Usage:
```bash
# Ensure required environment variables for your LLM models are set (e.g., CBORG_API_KEY, CBORG_API_URL).
python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow <flow_name> [<flow_name2> ...] \
  [--eval-model <model_name>] \
  [--cases-dir <dir1> --cases-dir <dir2> ...] \
  [--qa-file <qa.jsonl> ...] \
  [--passing-score 80] \
  [--output results.json]
```

Arguments:
- `--config`: Path to the ATHOS YAML config file (default: `config/config.yaml`).
- `--flow`: One or more execution flow names to test (required).
- `--eval-model`: Optional override model name for evaluation (defaults to the model used by each flow).
- `--cases-dir`: Directory containing structured test case subdirectories. May be provided multiple times. Defaults to `test_cases` if no datasets are specified.
- `--qa-file`: Path to a JSON Lines file of question/answer pairs. May be provided multiple times.
- `--passing-score`: Score threshold used when computing accuracy (default: `80`).
- `--output`: File path to write a JSON report of results.

## Available test cases

Current examples included in this repo:
- `hf-home-hang`
- `pytorch-launch-error`
- `pytorch-launch-error-2`
- `sbatch-qos-error`
- `vasp-license-error`
- `salloc-account-error`
- `gpu-misconfiguration`
