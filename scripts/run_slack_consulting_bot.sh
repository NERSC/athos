#!/usr/bin/env bash
# Usage: scripts/run_slack_consulting_bot.sh [--mode production|sandbox] [sandbox options]
#   production (default): the Slack bot, connected to Slack over Socket Mode.
#   sandbox: the same bot on a local web page, no Slack tokens or connection;
#            see `python -m athos.integrations.slack.sandbox --help` for its options.
# ATHOS_SLACK_MODE sets the mode when --mode is not given.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mode="${ATHOS_SLACK_MODE:-production}"
if [[ "${1:-}" == "--mode" ]]; then
  mode="${2:?--mode needs production or sandbox}"
  shift 2
elif [[ "${1:-}" == --mode=* ]]; then
  mode="${1#--mode=}"
  shift
fi

: "${ATHOS_CONFIG_PATH:=config/config.yaml}"
: "${ATHOS_FLOW_NAME:=lang_hpc_consulting_agent}"
: "${ATHOS_NOTE_WRITER_FLOW:=lang_hpc_note_writer}"
: "${ATHOS_FEEDBACK_DB:=data/slack/feedback.db}"
export ATHOS_CONFIG_PATH ATHOS_FLOW_NAME ATHOS_NOTE_WRITER_FLOW ATHOS_FEEDBACK_DB

# Use this checkout even when the environment's editable install points elsewhere.
export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"

case "$mode" in
  production)
    python -m athos.integrations.slack.consulting_bot
    ;;
  sandbox)
    python -m athos.integrations.slack.sandbox "$@"
    ;;
  *)
    echo "Unknown mode '$mode': use production or sandbox." >&2
    exit 2
    ;;
esac
