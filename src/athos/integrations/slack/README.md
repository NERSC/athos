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
`ATHOS_FLOW_NAME`, `ATHOS_NOTE_WRITER_FLOW`, and `ATHOS_FEEDBACK_DB`. It never
stores credentials. It puts this checkout's `src/` first on `PYTHONPATH`, so it
runs this code even if the environment's editable install points elsewhere.

While the bot works on a request it adds an :hourglass_flowing_sand: reaction
to the message.

## Notes

To keep a thread as a note, mention the bot in that thread and ask in your own
words, e.g. `@ATHOS take a note` or `@ATHOS note this conversation`. The
consulting flow recognizes the request and calls its `take_thread_note` tool,
and the bot then:

1. Reads the thread's earlier messages with `conversations.replies`. If there
   are none (the request starts a new thread), it replies that there is
   nothing to note.
2. Sends the thread to the `lang_hpc_note_writer` flow, which summarizes it
   into a question, the final answer (later corrections win) and the approach,
   and saves it with `note_taker` as `<notes dir>/<name>/note.md`. If a similar
   note exists, the writer updates it, keeps it, or saves a new one.
3. Replies with the saved note's name, or that the thread had nothing worth
   noting.

Reading threads needs the `channels:history`, `groups:history`, `im:history`
and `mpim:history` bot scopes; without them a note request fails with a
"couldn't read this thread" reply.

The consulting flow also has the `list_notes` and `read_note` tools and checks
notes before Chroma retrieval. An answer that came only from notes ends with an
_Answered from saved note_ footer.

Notes live in `$ATHOS_NOTES_DIR`, or `.notes/` at the repository root when it is
unset.

The bot records thumbs-up/down feedback in the configured SQLite database.
That database contains questions and responses, so place it in an appropriate
access-controlled location for a deployed instance.
