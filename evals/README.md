# ATHOS evaluations

This directory contains test cases and a script for evaluating ATHOS agent flows on common HPC troubleshooting scenarios.

Run the evaluation script to execute a specified flow on all test cases and grade the responses against the reference solutions.

Usage:
```bash
# Ensure required environment variables for your LLM models are set (e.g., CBORG_API_KEY, CBORG_API_URL).
python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow <flow_name> \
  [--eval-model <model_name>] \
  [--cases-dir test_cases] \
  [--output results.json]
```

Arguments:
- `--config`: Path to the ATHOS YAML config file (default: `config/config.yaml`).
- `--flow`: Name of the execution flow to test (required).
- `--eval-model`: Optional override model name for evaluation (defaults to the model used by the flow).
- `--cases-dir`: Directory containing test case subdirectories (default: `test_cases`).
- `--output`: File path to write a JSON report of results.

## Available test cases

Current examples included in this repo:
- `hf-home-hang`
- `pytorch-launch-error`
- `pytorch-launch-error-2`
- `sbatch-qos-error`
- `vasp-license-error`
- `salloc-account-error`
