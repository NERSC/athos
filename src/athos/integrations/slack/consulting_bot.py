"""Slack adapter for the read-only ATHOS consulting flow."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from collections.abc import Collection
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any

from anyio.from_thread import BlockingPortal, start_blocking_portal
from dotenv import load_dotenv

from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner
from athos.utils.note_writer import (
    NOTHING_TO_NOTE_MARKER,
    build_thread_message,
    note_saved,
    notes_answered_from,
    thread_note_requested,
    turn_steps,
)

from .feedback import FeedbackStore
from .runtime import (
    MAX_BLOCK_TEXT_LEN,
    REQUEST_FAILURE_TEXT,
    SlackInteractionRequest,
    SlackInteractionResponse,
    SlackMessagePost,
    SlackMessageRequest,
    SlackMessageResponse,
    SlackThreadMessage,
    SlackViewSubmissionRequest,
    SlackViewSubmissionResponse,
    flatten_input_values,
    run_socket_mode_app,
)


FEEDBACK_MODAL_CALLBACK_ID = "athos_consulting_feedback_detail"
FEEDBACK_TEXT_ACTION_ID = "feedback_text_input"
BUTTON_VALUE_MAX_LEN = 2000
PRIVATE_METADATA_MAX_LEN = 3000
UNAUTHORIZED_USER_TEXT = ":no_entry: You are not authorized to use this ATHOS app."
NOTHING_TO_NOTE_TEXT = "There's nothing to note in this thread yet. 📝"
NOTE_FAILURE_TEXT = "I couldn't save a note from this thread. ⚠️"
THREAD_MESSAGE_MAX_LEN = 4000

logger = logging.getLogger(__name__)


def slack_session_id(request: SlackMessageRequest) -> str:
    """Return a stable conversation ID for a Slack thread."""
    return f"{request.channel}:{request.thread_ts or request.event_ts or 'unknown'}"


def _bounded_json(data: dict[str, Any], max_length: int, *shrink_fields: str) -> str:
    """Serialize valid JSON, shortening selected text fields to fit."""
    data = data.copy()
    while len(encoded := json.dumps(data, separators=(",", ":"), ensure_ascii=False)) > max_length:
        overflow = len(encoded) - max_length
        for field in shrink_fields:
            value = data.get(field)
            if isinstance(value, str) and value:
                data[field] = value[: max(0, len(value) - overflow)]
                break
        else:
            raise ValueError("Feedback metadata exceeds Slack's size limit")
    return encoded


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


def _answered_from_notes_line(names: list[str]) -> str:
    """Footer marking a reply that came from saved notes."""
    label = "note" if len(names) == 1 else "notes"
    return f"_📝 Answered from saved {label}: {', '.join(f'`{name}`' for name in names)}_"


def _transcript(messages: list[SlackThreadMessage]) -> list[tuple[str, str]]:
    """(speaker, text) pairs, with ATHOS's own replies marked as such."""
    return [
        (
            "ATHOS" if message.from_bot else f"<@{message.user_id or 'unknown'}>",
            message.text[:THREAD_MESSAGE_MAX_LEN],
        )
        for message in messages
    ]

class AthosConsultingSlackAdapter:
    """Bridge Slack requests to a configured ATHOS consulting flow."""

    app_name = "athos-consulting"
    empty_prompt = "Mention an incident number or ask a consulting question in this thread."

    def __init__(
        self,
        runner: FlowRunner,
        *,
        portal: BlockingPortal,
        allowed_users: Collection[str],
        flow_name: str = "lang_hpc_consulting_agent",
        feedback_store: FeedbackStore | None = None,
        note_writer_flow: str = "lang_hpc_note_writer",
    ) -> None:
        self._runner = runner
        self._portal = portal
        self._flow_name = flow_name
        self._feedback_store = feedback_store
        self._note_writer_flow = note_writer_flow
        self._session_locks: dict[str, asyncio.Lock] = {}
        self._allowed_users = frozenset(user.strip() for user in allowed_users if user.strip())
        if not self._allowed_users:
            raise ValueError("ATHOS_SLACK_ALLOWED_USERS must contain at least one Slack user ID")

    async def _execute(self, request: SlackMessageRequest, session_id: str):
        lock = self._session_locks.setdefault(session_id, asyncio.Lock())
        async with lock:
            return await self._runner.execute(
                flow_name=self._flow_name,
                message=request.question,
                session_id=session_id,
                user_id=request.user_id or "unknown",
                interface="slack",
                # The tool trace shows note requests and answers that came from notes.
                metadata={
                    "slack_channel": request.channel,
                    "slack_thread_ts": request.thread_ts,
                    "debug_include_steps": True,
                },
            )

    def handle_question(self, request: SlackMessageRequest) -> SlackMessageResponse:
        if request.user_id not in self._allowed_users:
            return SlackMessageResponse(text=UNAUTHORIZED_USER_TEXT)
        session_id = slack_session_id(request)
        result = self._portal.call(partial(self._execute, request, session_id))
        if (
            not result.success
            or result.output is None
            or result.output.metadata.get("error")
        ):
            return SlackMessageResponse(text=REQUEST_FAILURE_TEXT)

        steps = turn_steps(result.output.metadata.get("langgraph_steps") or [])
        if thread_note_requested(steps):
            return SlackMessageResponse(text=self._note_thread(request))
        response_text = normalize_slack_mrkdwn(result.output.content)
        note_names = notes_answered_from(steps)
        if note_names:
            response_text += "\n\n" + _answered_from_notes_line(note_names)
        detached = len(response_text) > MAX_BLOCK_TEXT_LEN
        feedback_payload = {
            "session_id": session_id,
            "question": request.question[:500],
            "detached": detached,
        }
        if detached:
            feedback_payload["response_text"] = response_text
        feedback_value = _bounded_json(
            feedback_payload,
            BUTTON_VALUE_MAX_LEN,
            "response_text",
            "question",
        )
        if detached:
            return SlackMessageResponse(
                text=response_text,
                followup_posts=[
                    SlackMessagePost(
                        text="Was this response helpful?",
                        blocks=self._feedback_blocks(feedback_value),
                    )
                ],
            )
        return SlackMessageResponse(
            text=response_text,
            blocks=self._feedback_blocks(feedback_value, response_text=response_text),
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

    def _note_thread(self, request: SlackMessageRequest) -> str:
        """Have the note-writer flow summarize the thread into a note; return the reply."""
        try:
            messages = request.thread_history() if request.thread_history else []
        except Exception:  # noqa: BLE001
            logger.exception("Failed to read Slack thread for a note")
            return "I couldn't read this thread to take a note. ⚠️"
        if not messages:
            return NOTHING_TO_NOTE_TEXT
        try:
            result = self._portal.call(
                partial(
                    self._runner.execute,
                    flow_name=self._note_writer_flow,
                    message=build_thread_message(_transcript(messages)),
                    session_id=f"note-writer-{uuid.uuid4().hex[:12]}",
                    user_id=request.user_id or "unknown",
                    interface="slack",
                    metadata={"debug_include_steps": True},
                )
            )
        except Exception:  # noqa: BLE001
            logger.exception("Note writer flow failed")
            return NOTE_FAILURE_TEXT
        if not result.success or result.output is None or result.output.metadata.get("error"):
            logger.warning("Note writer flow failed: %s", getattr(result, "error", None))
            return NOTE_FAILURE_TEXT
        saved = note_saved(result.output.metadata.get("langgraph_steps") or [])
        if saved is None:
            logger.info("Note writer saved nothing: %r", result.output.content[:300])
            if NOTHING_TO_NOTE_MARKER in result.output.content.upper():
                return NOTHING_TO_NOTE_TEXT
            return NOTE_FAILURE_TEXT
        action, name = saved
        logger.info("%s note %r from thread %s", action.capitalize(), name, slack_session_id(request))
        if action == "unchanged":
            return f"Note `{name}` already covers this thread, so I left it as is. 📝"
        return f"{'Saved' if action == 'created' else 'Updated'} this thread as note `{name}`. 📝"

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
        detached = bool(payload.get("detached"))
        response_text = payload.get("response_text", "") if detached else message.get("text", "")
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
            if detached:
                return SlackInteractionResponse(
                    replace_original=SlackMessagePost("Thanks for the feedback! 👍")
                )
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": response_text}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": "Thanks for the feedback! 👍"}]},
            ]
            return SlackInteractionResponse(replace_original=SlackMessagePost(response_text, blocks))

        metadata = _bounded_json(
            {
                "channel": request.channel,
                "message_ts": request.message_ts,
                "thread_ts": request.thread_ts,
                "session_id": payload.get("session_id"),
                "question": payload.get("question"),
                "response_text": response_text,
            },
            PRIVATE_METADATA_MAX_LEN,
            "response_text",
            "question",
        )
        acknowledgement = "Thanks for the feedback. Tell us more in the form if useful. ✏️"
        replacement = SlackMessagePost(acknowledgement)
        if not detached:
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": response_text}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": acknowledgement}]},
            ]
            replacement = SlackMessagePost(response_text, blocks)
        return SlackInteractionResponse(
            replace_original=replacement,
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
    note_writer_flow = os.getenv("ATHOS_NOTE_WRITER_FLOW", "lang_hpc_note_writer")
    feedback_db = Path(os.getenv("ATHOS_FEEDBACK_DB", "data/slack/feedback.db"))
    allowed_users = os.getenv("ATHOS_SLACK_ALLOWED_USERS", "").split(",")
    runner = FlowRunner(build_config(config_path))
    with start_blocking_portal(backend="asyncio", name="athos-slack-asyncio") as portal:
        adapter = AthosConsultingSlackAdapter(
            runner,
            portal=portal,
            allowed_users=allowed_users,
            flow_name=flow_name,
            feedback_store=FeedbackStore(feedback_db),
            note_writer_flow=note_writer_flow,
        )
        try:
            run_socket_mode_app(adapter)
        finally:
            portal.call(runner.cleanup)


if __name__ == "__main__":
    main()
