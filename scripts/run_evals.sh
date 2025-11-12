#!/bin/bash

python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow langgraph_chatbot_demo \
  --cases-dir evals/test_cases \
  --qa-file evals/simple_qa.jsonl \
  --output logs/eval_results.json
