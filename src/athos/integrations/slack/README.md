# ATHOS Slack consulting integration

This package runs an ATHOS flow as a Slack Socket Mode application. It handles
app mentions, direct messages, and the `/athos-consulting` command, keeping
conversation history scoped to a Slack thread.

The default flow is `lang_hpc_consulting_agent`, which is configured with
read-only ServiceNow and Chroma MCP servers in `config/config.yaml`.

## Local run

Install the optional dependency and put the Slack and ATHOS credentials in
`.env` (see `.env.template`):

```bash
pip install -e '.[slack]'
scripts/run_slack_consulting_bot.sh
```

The launcher accepts environment overrides for `ATHOS_CONFIG_PATH`,
`ATHOS_FLOW_NAME`, and `ATHOS_FEEDBACK_DB`. It never stores credentials.

The bot records thumbs-up/down feedback in the configured SQLite database.
That database contains questions and responses, so place it in an appropriate
access-controlled location for a deployed instance.
