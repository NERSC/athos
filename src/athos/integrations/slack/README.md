# ATHOS Slack consulting integration

This package runs an ATHOS flow as a Slack Socket Mode application. It handles
app mentions and direct messages, keeping conversation history scoped to a
Slack thread.

The default flow is `lang_hpc_consulting_agent`, which is configured with
read-only ServiceNow and Chroma MCP servers in `config/config.yaml`.

## Local run

Install the optional dependency and put the Slack and ATHOS credentials in
`.env` (see `.env.template`):

```bash
pip install -e '.[slack]'
scripts/run_slack_consulting_bot.sh
```

Set `ATHOS_SLACK_ALLOWED_USERS` to the comma-separated Slack member IDs that
may use the bot. The bot refuses to start with an empty allowlist and sends a
fixed denial response without running the flow for any other user. Keep the
deployment's actual IDs in `.env`; only the example belongs in the repository.

The launcher also accepts environment overrides for `ATHOS_CONFIG_PATH`,
`ATHOS_FLOW_NAME`, and `ATHOS_FEEDBACK_DB`. It never stores credentials.

The bot records thumbs-up/down/take note feedback in the configured SQLite database.
That database contains questions and responses, so place it in an appropriate
access-controlled location for a deployed instance.
