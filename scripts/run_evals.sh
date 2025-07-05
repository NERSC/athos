#!/bin/bash

python evals/run_evaluations.py \
  --config config/config.yaml \
  --flow hpc_chatbot web_agent \
  --output eval_results.json
