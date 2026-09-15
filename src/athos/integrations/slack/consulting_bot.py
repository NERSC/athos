"""Slack adapter for the read-only ATHOS consulting flow."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any

from anyio.from_thread import BlockingPortal, start_blocking_portal
from dotenv import load_dotenv

from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner

from .feedback import FeedbackStore
from .runtime import (
    MAX_BLOCK_TEXT_LEN,
    SlackInteractionRequest,
    SlackInteractionResponse,
    SlackMessagePost,
    SlackMessageRequest,
    SlackMessageResponse,
    SlackViewSubmissionRequest,
    SlackViewSubmissionResponse,
    flatten_input_values,
    run_socket_mode_app,
)


FEEDBACK_MODAL_CALLBACK_ID = "athos_consulting_feedback_detail"
FEEDBACK_TEXT_ACTION_ID = "feedback_text_input"


def slack_session_id(request: SlackMessageRequest) -> str:
    """Return a stable conversation ID for a Slack thread."""
    return f"{request.channel}:{request.thread_ts or request.event_ts or 'unknown'}"

def normalize_slack_mrkdwn(text: str) -> str:
    text = re.sub(
        r"&#x20;|&#32;|&nbsp;",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # \### -> ###, \*\* -> **, 1\. -> 1.
    text = re.sub(r"\\([#*_~.\-])", r"\1", text)

    # ### Heading -> *Heading*
    text = re.sub(
        r"(?m)^\s*#{1,6}\s+(.+?)\s*$",
        lambda match: f"*{match.group(1).strip()}*",
        text,
    )

    # **text** -> *text*
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)

    # [label](URL) -> <URL|label>
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r"<\2|\1>",
        text,
    )

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

class AthosConsultingSlackAdapter:
    """Bridge Slack requests to a configured ATHOS consulting flow."""

    app_name = "athos-consulting"
    empty_prompt = "Mention an incident number or ask a consulting question in this thread."

    def __init__(
        self,
        runner: FlowRunner,
        *,
        portal: BlockingPortal,
        flow_name: str = "lang_hpc_consulting_agent",
        feedback_store: FeedbackStore | None = None,
    ) -> None:
        self._runner = runner
        self._portal = portal
        self._flow_name = flow_name
        self._feedback_store = feedback_store

    def handle_question(self, request: SlackMessageRequest) -> SlackMessageResponse:
        session_id = slack_session_id(request)
        result = self._portal.call(
            partial(
                self._runner.execute,
                flow_name=self._flow_name,
                message=request.question,
                session_id=session_id,
                user_id=request.user_id or "unknown",
                interface="slack",
                metadata={"slack_channel": request.channel, "slack_thread_ts": request.thread_ts},
            )
        )
        if (
            not result.success
            or result.output is None
            or result.output.metadata.get("error")
        ):
            return SlackMessageResponse(
                text=":warning: I could not complete that consulting request. Please check the bot logs or try again shortly."
            )

        response_text = normalize_slack_mrkdwn(result.output.content)
        feedback_value = json.dumps(
            {
                "session_id": session_id,
                "question": request.question[:500],
                "response_text": response_text[:1500],
            }
        )[:2000]
        if len(response_text) > MAX_BLOCK_TEXT_LEN:
            return SlackMessageResponse(
                text=response_text,
                followup_posts=[
                    SlackMessagePost(
                        text="Was this response helpful?",
                        blocks=self._feedback_blocks(feedback_value),
                    )
                ],
                terminal_fields={"channel": request.channel, "thread_ts": request.thread_ts, "user_id": request.user_id},
            )
        return SlackMessageResponse(
            text=response_text,
            blocks=self._feedback_blocks(feedback_value, response_text=response_text),
            terminal_fields={"channel": request.channel, "thread_ts": request.thread_ts, "user_id": request.user_id},
        )

    @staticmethod
    def _feedback_blocks(feedback_value: str, *, response_text: str | None = None) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        if response_text is not None:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": response_text}})
        blocks.append(
            {
                "type": "actions",
                "block_id": "athos_consulting_feedback",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👍", "emoji": True},
                        "action_id": "feedback_up",
                        "value": feedback_value,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👎", "emoji": True},
                        "action_id": "feedback_down",
                        "value": feedback_value,
                    },
                ],
            }
        )
        return blocks

    def _record_feedback(self, entry: dict[str, Any]) -> None:
        if self._feedback_store is not None:
            self._feedback_store.record({"timestamp": datetime.now(timezone.utc).isoformat(), **entry})

    def handle_interaction(self, request: SlackInteractionRequest) -> SlackInteractionResponse | None:
        if request.action_id not in {"feedback_up", "feedback_down"}:
            return None
        try:
            payload = json.loads(request.action_value or "{}")
        except json.JSONDecodeError:
            payload = {}
        rating = "up" if request.action_id == "feedback_up" else "down"
        message = request.context.get("message") or {}
        response_text = payload.get("response_text") or message.get("text", "")
        self._record_feedback(
            {
                "rating": rating,
                "kind": "rating",
                "channel": request.channel,
                "message_ts": request.message_ts,
                "reactor_user_id": request.user_id,
                "username": (request.raw_payload.get("user") or {}).get("username", "unknown"),
                "session_id": payload.get("session_id"),
                "question": payload.get("question"),
                "response_text": response_text,
                "comment": None,
            }
        )
        if rating == "up":
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": response_text}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": "Thanks for the feedback! 👍"}]},
            ]
            return SlackInteractionResponse(replace_original=SlackMessagePost(response_text, blocks))

        metadata = json.dumps(
            {
                "channel": request.channel,
                "message_ts": request.message_ts,
                "thread_ts": request.thread_ts,
                "session_id": payload.get("session_id"),
                "question": payload.get("question"),
                "response_text": response_text[:1500],
            }
        )[:3000]
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": response_text}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Thanks for the feedback. Tell us more in the form if useful. ✏️"}]},
        ]
        return SlackInteractionResponse(
            replace_original=SlackMessagePost(response_text, blocks),
            open_view={
                "type": "modal",
                "callback_id": FEEDBACK_MODAL_CALLBACK_ID,
                "private_metadata": metadata,
                "title": {"type": "plain_text", "text": "Feedback"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": [{"type": "input", "block_id": "feedback_text_block", "optional": True, "label": {"type": "plain_text", "text": "What went wrong? (optional)"}, "element": {"type": "plain_text_input", "action_id": FEEDBACK_TEXT_ACTION_ID, "multiline": True}}],
            },
        )

    def handle_view_submission(self, request: SlackViewSubmissionRequest) -> SlackViewSubmissionResponse | None:
        if request.callback_id != FEEDBACK_MODAL_CALLBACK_ID:
            return None
        try:
            metadata = json.loads(request.private_metadata or "{}")
        except json.JSONDecodeError:
            metadata = {}
        comment = flatten_input_values(request.values).get(FEEDBACK_TEXT_ACTION_ID, "").strip()
        if not comment:
            return None
        self._record_feedback(
            {
                "rating": "down",
                "kind": "comment",
                "channel": metadata.get("channel"),
                "message_ts": metadata.get("message_ts"),
                "reactor_user_id": request.user_id,
                "username": (request.raw_payload.get("user") or {}).get("username", "unknown"),
                "session_id": metadata.get("session_id"),
                "question": metadata.get("question"),
                "response_text": metadata.get("response_text"),
                "comment": comment,
            }
        )
        if not metadata.get("channel"):
            return SlackViewSubmissionResponse()
        return SlackViewSubmissionResponse(
            thread_posts=[SlackMessagePost("Thanks for the detailed feedback 🙏", channel=metadata["channel"], thread_ts=metadata.get("thread_ts") or metadata.get("message_ts"))]
        )


def main() -> None:
    """Start the Slack consulting bot using environment-based configuration."""
    load_dotenv()
    config_path = os.getenv("ATHOS_CONFIG_PATH", "config/config.yaml")
    flow_name = os.getenv("ATHOS_FLOW_NAME", "lang_hpc_consulting_agent")
    feedback_db = Path(os.getenv("ATHOS_FEEDBACK_DB", "data/slack/feedback.db"))
    runner = FlowRunner(build_config(config_path))
    with start_blocking_portal(backend="asyncio", name="athos-slack-asyncio") as portal:
        adapter = AthosConsultingSlackAdapter(
            runner,
            portal=portal,
            flow_name=flow_name,
            feedback_store=FeedbackStore(feedback_db),
        )
        try:
            run_socket_mode_app(adapter)
        finally:
            portal.call(runner.cleanup)


if __name__ == "__main__":
    main()
