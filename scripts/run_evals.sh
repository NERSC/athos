#!/bin/bash

python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow hpc_chatbot web_agent \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --output eval_results.json
