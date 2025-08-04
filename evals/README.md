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
- `--qa-file`: JSONL file of question/answer pairs. May be provided multiple times.
- `--passing-score`: Score threshold used when computing accuracy (default: `80`).
- `--output`: File path to write a JSON report of results.

### Running specific datasets

- **HPC troubleshooting cases only** (default):
  ```bash
  python evals/run_evaluations.py --config config/config.yaml --flow hpc_chatbot
  ```
- **Q&A cases only**:
  ```bash
  python evals/run_evaluations.py --config config/config.yaml --flow hpc_chatbot --qa-file evals/simple_qa.jsonl
  ```
- **Both HPC and Q&A cases**:
  ```bash
  python evals/run_evaluations.py --config config/config.yaml --flow hpc_chatbot --cases-dir evals/test_cases --qa-file evals/simple_qa.jsonl
  ```

## Available test cases

Current examples included in this repo:
- `hf-home-hang`
- `pytorch-launch-error`
- `pytorch-launch-error-2`
- `sbatch-qos-error`
- `vasp-license-error`
- `salloc-account-error`
- `gpu-misconfiguration`
