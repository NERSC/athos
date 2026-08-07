#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

: "${ATHOS_CONFIG_PATH:=config/config.yaml}"
: "${ATHOS_FLOW_NAME:=lang_hpc_consulting_agent}"
: "${ATHOS_FEEDBACK_DB:=data/slack/feedback.db}"
export ATHOS_CONFIG_PATH ATHOS_FLOW_NAME ATHOS_FEEDBACK_DB

python -m athos.integrations.slack.consulting_bot
