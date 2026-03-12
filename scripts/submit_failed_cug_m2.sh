#!/bin/bash

EXPERIMENT_ID=cug_m2_20260308_230032 \
  FLOWS='cug_lang_chroma_sonnet' \
  RUN_START=1 RUN_COUNT=1 \
  CASES_DIRS='/pscratch/sd/s/sfarrell/athos/data/ticket_cases_failed_cug_m2_20260308_230032_cug_lang_chroma_sonnet__claude_sonnet__7034e2f0' \
  QA_FILES='evals/nersc_qa.v2.jsonl' \
  scripts/run_cug_m2.sh
