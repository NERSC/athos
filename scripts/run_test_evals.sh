#!/bin/bash

# This script is for running a minimal test of the evals pipeline.

python evals/run_evaluations.py \
  --config config/config.yaml \
  --eval-model cborg_chat \
  --flow lang_chat \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --output logs/eval_results.json
