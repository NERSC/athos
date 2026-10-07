# ATHOS Slack consulting integration

This package handles app mentions, direct messages, and the
`/athos-consulting` command through Slack Socket Mode. The active sandbox
chooses one of five fixed question-answer pairs for each query, prints the
selection in the terminal, and records it in the feedback database. The ATHOS
consulting flow call is commented out in `consulting_bot.py`.

## Local run

Install the optional dependency and put the Slack and ATHOS credentials in
`.env` (see `.env.template`):

```bash
pip install -e '.[slack]'
scripts/run_slack_consulting_bot.sh
```

The sandbox uses `ATHOS_FEEDBACK_DB` for selection notes. The launcher also
sets flow variables for the commented-out consulting pipeline.

The sandbox records each selected pair in the configured SQLite database.
That database contains questions and responses, so place it in an appropriate
access-controlled location for a deployed instance.
