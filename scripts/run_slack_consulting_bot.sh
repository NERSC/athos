#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

: "${ATHOS_CONFIG_PATH:=config/paper/cug_m1.yaml}"
: "${ATHOS_FLOW_NAME:=cug_lang_chroma_gptoss_opt}"
: "${ATHOS_NOTE_WRITER_FLOW:=cug_note_writer_gptoss}"
: "${ATHOS_FEEDBACK_DB:=data/slack/feedback.db}"
export ATHOS_CONFIG_PATH ATHOS_FLOW_NAME ATHOS_NOTE_WRITER_FLOW ATHOS_FEEDBACK_DB

# Use this checkout even when the environment's editable install points elsewhere.
export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"

python -m athos.integrations.slack.consulting_bot
