#!/bin/bash

# Using this script to run whatever my current debugging test is...

# Bad collection name retrieval
athos \
     --config config/paper/cug_m1.yaml \
     --flow cug_lang_chroma_sonnet \
     --input "What type of GPUs are in the Perlmutter supercomputer?" \
     -v 2>&1 | tee ./logs/repro_chroma_perlmutter_gpus.log
#--flow cug_lang_chroma_gptoss 

# Empty chroma db?
#python evals/run_evaluations.py \
#     --config config/paper/cug_m1.yaml \
#     --flow cug_lang_chroma_sonnet \
#     --qa-file ./tmp/perlmutter_gpus.jsonl \
#     --output-dir results/debug \
#     --experiment-id debugging-$(date +%Y%m%d_%H%M%S)
