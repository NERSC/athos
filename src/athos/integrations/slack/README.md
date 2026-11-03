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

## Sandbox mode

To try the bot without Slack, run it in sandbox mode. It needs no Slack
tokens and never connects to Slack:

```bash
scripts/run_slack_consulting_bot.sh --mode sandbox   # or ATHOS_SLACK_MODE=sandbox
# then open http://127.0.0.1:8765
```

`production` is the default mode and runs the Slack bot exactly as before.

The sandbox serves a one-channel, Slack-like page. It builds the same adapter
and flows as production from the same `ATHOS_CONFIG_PATH`, `ATHOS_FLOW_NAME`
and `ATHOS_NOTE_WRITER_FLOW`. An in-memory workspace
(`athos.integrations.slack.sandbox`) stands in for Slack's Web API, so
messages go through the production runtime's own code: mention detection,
thread history, the working reaction, long-reply splitting, the feedback
buttons, message updates and the feedback modal.

- Mention `@athos` to ask the bot. Messages without a mention are posted to the
  thread without a reply, and the bot reads them when asked to take a note.
- "You are" sets the user you post as. The bot answers only the sandbox's
  allowed users (`USANDBOX` by default, `--allowed-users` to change), so any
  other ID shows the unauthorized reply.
- The page keeps nothing. Every start begins with an empty channel, and an open
  page reloads when the sandbox restarts.
- Notes and feedback go to `data/slack_sandbox/notes` and
  `data/slack_sandbox/feedback.db`, apart from production's. Use `--notes-dir`
  and `--feedback-db`, or `ATHOS_SANDBOX_NOTES_DIR` and
  `ATHOS_SANDBOX_FEEDBACK_DB`, to point elsewhere, such as a copy of the
  production notes.
- It listens on `127.0.0.1:8765` (`--host`, `--port`). From a NERSC login node,
  forward the port to view it: `ssh -L 8765:localhost:8765 perlmutter`.

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
   and saves it with `note_taker` in the notes Chroma collection. If a similar
   note exists, the writer updates it, keeps it, or saves a new one.
3. Replies with the saved note's name, or that the thread had nothing worth
   noting.

Reading threads needs the `channels:history`, `groups:history`, `im:history`
and `mpim:history` bot scopes; without them a note request fails with a
"couldn't read this thread" reply.

The consulting flow also has the `list_notes` and `read_note` tools and checks
notes before Chroma retrieval. An answer that came only from notes ends with an
_Answered from saved note_ footer.

Notes live in the `consulting_notes` collection of a Chroma database at
`$ATHOS_NOTES_CHROMA_DIR`, or `<notes dir>/chroma` when it is unset, where the
notes directory is `$ATHOS_NOTES_DIR` or `.notes/` at the repository root.
`list_notes` matches them by meaning as well as by exact error text, job ID or
tag. Notes saved as `<notes dir>/<name>/note.md` by earlier versions are
imported the first time the collection is empty.

Flows reach the notes through the notes MCP server (`athos.tools.notes_mcp`):
the note writer through `notes_mcp`, which allows only `note_taker`, and the
consulting flow through the read-only `notes_ro_mcp` (`list_notes`,
`read_note`). The server runs over stdio, so every tool call is a fresh
process that opens the database: a saved note is searchable on the next
question, with no restart. A file lock beside the database keeps overlapping
calls from touching it at once. Each call takes a few seconds, most of it
loading the embedding model. The notes database is separate from the
retrieval databases that `chroma_mcp` and `consulting_chroma_ro_mcp` serve.

The bot records thumbs-up/down feedback in the configured SQLite database.
That database contains questions and responses, so place it in an appropriate
access-controlled location for a deployed instance.
