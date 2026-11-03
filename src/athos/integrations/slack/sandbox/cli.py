"""Run the ATHOS consulting Slack bot in the local sandbox instead of Slack.

It builds the same adapter, flows and runner as the production bot
(consulting_bot.main) from the same ATHOS_CONFIG_PATH, ATHOS_FLOW_NAME and
ATHOS_NOTE_WRITER_FLOW settings, and serves it on a local web page. It
needs no Slack tokens and never connects to Slack.

So that trying things out does not touch the production bot's data, it
keeps its own notes and feedback under data/slack_sandbox/ by default
(ATHOS_SANDBOX_NOTES_DIR, ATHOS_SANDBOX_FEEDBACK_DB, or --notes-dir and
--feedback-db), and the only allowed users are the sandbox's own.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .server import DEFAULT_USER_ID, serve

DEFAULT_NOTES_DIR = "data/slack_sandbox/notes"
DEFAULT_FEEDBACK_DB = "data/slack_sandbox/feedback.db"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ATHOS consulting Slack bot, sandbox mode")
    parser.add_argument("--host", default=os.getenv("ATHOS_SANDBOX_HOST", "127.0.0.1"), help="Address to serve on (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.getenv("ATHOS_SANDBOX_PORT", "8765")), help="Port to serve on (default 8765)")
    parser.add_argument(
        "--notes-dir",
        default=os.getenv("ATHOS_SANDBOX_NOTES_DIR", DEFAULT_NOTES_DIR),
        help=f"Notes directory for the sandbox (default {DEFAULT_NOTES_DIR})",
    )
    parser.add_argument(
        "--feedback-db",
        default=os.getenv("ATHOS_SANDBOX_FEEDBACK_DB", DEFAULT_FEEDBACK_DB),
        help=f"Feedback database for the sandbox (default {DEFAULT_FEEDBACK_DB})",
    )
    parser.add_argument(
        "--allowed-users",
        default=os.getenv("ATHOS_SANDBOX_ALLOWED_USERS", DEFAULT_USER_ID),
        help=f"Comma-separated sandbox user IDs the bot answers (default {DEFAULT_USER_ID})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Before the config is built: config.yaml expands ${ATHOS_NOTES_DIR} into the notes MCP servers' args.
    os.environ["ATHOS_NOTES_DIR"] = str(Path(args.notes_dir).resolve())
    os.environ.pop("ATHOS_NOTES_CHROMA_DIR", None)

    # Imported here so `--help` works without loading the runtime.
    from anyio.from_thread import start_blocking_portal

    from athos.runtime.builder import build_config
    from athos.runtime.runner import FlowRunner

    from ..consulting_bot import AthosConsultingSlackAdapter
    from ..feedback import FeedbackStore

    config_path = os.getenv("ATHOS_CONFIG_PATH", "config/config.yaml")
    flow_name = os.getenv("ATHOS_FLOW_NAME", "lang_hpc_consulting_agent")
    note_writer_flow = os.getenv("ATHOS_NOTE_WRITER_FLOW", "lang_hpc_note_writer")
    print(
        f"Sandbox: config {config_path}, flow {flow_name}, note writer {note_writer_flow}, "
        f"notes {os.environ['ATHOS_NOTES_DIR']}, feedback {Path(args.feedback_db).resolve()}"
    )
    runner = FlowRunner(build_config(config_path))
    with start_blocking_portal(backend="asyncio", name="athos-slack-sandbox-asyncio") as portal:
        adapter = AthosConsultingSlackAdapter(
            runner,
            portal=portal,
            allowed_users=args.allowed_users.split(","),
            flow_name=flow_name,
            feedback_store=FeedbackStore(Path(args.feedback_db)),
            note_writer_flow=note_writer_flow,
        )
        try:
            serve(adapter, host=args.host, port=args.port)
        finally:
            portal.call(runner.cleanup)
