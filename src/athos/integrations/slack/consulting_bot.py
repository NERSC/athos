"""Slack consulting adapter (feedback, Take notes) and fixed-answer sandbox."""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner
from athos.tools.note_taker import save_approved_note
from athos.utils.note_writer import (
    build_writer_message,
    format_trace,
    parse_note_draft,
    tool_call_summary,
    turn_steps,
)

from .feedback import FeedbackStore
from .runtime import (
    MAX_BLOCK_TEXT_LEN,
    FunctionSlackAdapter,
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
FEEDBACK_BLOCK_ID = "athos_consulting_feedback"
TAKE_NOTES_ACTION_ID = "take_notes"


SANDBOX_QA_PAIRS = (
    ("What is ATHOS?", "ATHOS is a toolkit for HPC operations support."),
    ("How do I ask for help?", "Describe the issue and include any relevant error message."),
    ("What details should I include?", "Include the system, job ID, time, and steps to reproduce the issue."),
    ("Where can I check a job?", "Check your job's status with the scheduler's job commands."),
    ("What if the issue persists?", "Share the details with the support team for further help."),
)


def answer_sandbox_question(request: SlackMessageRequest, feedback_store: FeedbackStore) -> SlackMessageResponse:
    """Reply with a random fixed answer and record the selected example."""
    selected_question, answer = random.choice(SANDBOX_QA_PAIRS)
    print(f"Slack sandbox query: {request.question}\nSelected question: {selected_question}\nAnswer: {answer}", flush=True)
    feedback_store.record(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rating": None,
            "kind": "sandbox_selection",
            "channel": request.channel,
            "message_ts": request.event_ts,
            "reactor_user_id": request.user_id,
            "username": None,
            "session_id": slack_session_id(request),
            "question": request.question,
            "response_text": answer,
            "comment": f"Selected example question: {selected_question}",
        }
    )
    return SlackMessageResponse(text=answer)


def create_sandbox_adapter(feedback_store: FeedbackStore) -> FunctionSlackAdapter:
    """Connect the fixed-answer sandbox to the existing Slack runtime."""
    return FunctionSlackAdapter(
        lambda request: answer_sandbox_question(request, feedback_store),
        app_name="athos-consulting-sandbox",
        command_name="/athos-consulting",
        default_question="Ask a sandbox question.",
        empty_prompt="Ask a question and I will send a sample answer.",
    )


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

def _fit_feedback_value(session_id: str, question: str, response_text: str, run_id: str) -> str:
    """Button value as valid JSON within Slack's 2000-character limit."""
    for answer_limit in (1500, 1000, 500, 0):
        value = json.dumps(
            {
                "session_id": session_id,
                "question": question[:500],
                "response_text": response_text[:answer_limit],
                "run_id": run_id,
            }
        )
        if len(value) <= 2000:
            return value
    return json.dumps({"session_id": session_id, "run_id": run_id})


class AthosConsultingSlackAdapter:
    """Bridge Slack requests to a configured ATHOS consulting flow."""

    app_name = "athos-consulting"
    command_name = "/athos-consulting"
    default_question = "What incident or consulting question can I help with?"
    empty_prompt = "Mention an incident number or ask a consulting question in this thread."
    pending_actions = frozenset({TAKE_NOTES_ACTION_ID})

    def __init__(
        self,
        runner: FlowRunner,
        *,
        flow_name: str = "lang_hpc_consulting_agent",
        feedback_store: FeedbackStore | None = None,
        note_writer_flow: str = "lang_hpc_note_writer",
    ) -> None:
        self._runner = runner
        self._flow_name = flow_name
        self._feedback_store = feedback_store
        # Notes need the feedback store, which keeps each run for a later Take notes click.
        self._note_writer_flow = note_writer_flow

    def handle_question(self, request: SlackMessageRequest) -> SlackMessageResponse:
        session_id = slack_session_id(request)
        metadata: dict[str, Any] = {"slack_channel": request.channel, "slack_thread_ts": request.thread_ts}
        if self._feedback_store is not None:
            metadata["debug_include_steps"] = True  # tool trace for Take notes
        result = asyncio.run(
            self._runner.execute(
                flow_name=self._flow_name,
                message=request.question,
                session_id=session_id,
                user_id=request.user_id or "unknown",
                interface="slack",
                metadata=metadata,
            )
        )
        if not result.success or result.output is None:
            return SlackMessageResponse(
                text=":warning: I could not complete that consulting request. Please check the bot logs or try again shortly."
            )

        response_text = normalize_slack_mrkdwn(result.output.content)
        run_id = self._save_run(request, session_id, result.output)
        if run_id is None:
            feedback_value = json.dumps(
                {
                    "session_id": session_id,
                    "question": request.question[:500],
                    "response_text": response_text[:1500],
                }
            )[:2000]
        else:
            feedback_value = _fit_feedback_value(session_id, request.question, response_text, run_id)
        notes = run_id is not None
        if len(response_text) > MAX_BLOCK_TEXT_LEN:
            return SlackMessageResponse(
                text=response_text,
                followup_posts=[
                    SlackMessagePost(
                        text="Was this response helpful?",
                        blocks=self._feedback_blocks(feedback_value, notes=notes),
                    )
                ],
                terminal_fields={"channel": request.channel, "thread_ts": request.thread_ts, "user_id": request.user_id},
            )
        return SlackMessageResponse(
            text=response_text,
            blocks=self._feedback_blocks(feedback_value, response_text=response_text, notes=notes),
            terminal_fields={"channel": request.channel, "thread_ts": request.thread_ts, "user_id": request.user_id},
        )

    @staticmethod
    def _feedback_blocks(
        feedback_value: str, *, response_text: str | None = None, notes: bool = False
    ) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        if response_text is not None:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": response_text}})
        elements: list[dict[str, Any]] = [
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
        ]
        if notes:
            elements.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📝 Take notes", "emoji": True},
                    "action_id": TAKE_NOTES_ACTION_ID,
                    "value": feedback_value,
                }
            )
        blocks.append({"type": "actions", "block_id": FEEDBACK_BLOCK_ID, "elements": elements})
        return blocks

    @staticmethod
    def _blocks_after_click(
        message: dict[str, Any], response_text: str, used: set[str], line: str
    ) -> list[dict[str, Any]]:
        """Answer, any buttons not yet used, earlier status lines, then `line`.

        Keeps Take notes after a rating (and the ratings after Take notes), so
        they work in either order.
        """
        blocks: list[dict[str, Any]] = [{"type": "section", "text": {"type": "mrkdwn", "text": response_text}}]
        for block in message.get("blocks") or []:
            if block.get("type") == "actions" and block.get("block_id") == FEEDBACK_BLOCK_ID:
                remaining = [e for e in block.get("elements", []) if e.get("action_id") not in used]
                if remaining:
                    blocks.append({**block, "elements": remaining})
            elif block.get("type") == "context":
                blocks.append(block)
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": line}]})
        return blocks

    def _save_run(self, request: SlackMessageRequest, session_id: str, output: Any) -> str | None:
        """Keep the question, raw answer and this turn's tool trace; return its run ID."""
        if self._feedback_store is None:
            return None
        steps = turn_steps((getattr(output, "metadata", None) or {}).get("langgraph_steps") or [])
        run_id = uuid.uuid4().hex
        try:
            self._feedback_store.save_run(
                {
                    "run_id": run_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "session_id": session_id,
                    "user_id": request.user_id,
                    "question": request.question,
                    "answer": output.content,
                    "trace": json.dumps(steps, default=str),
                }
            )
        except Exception as exc:
            print(f"[notes] failed to record run: {exc}", flush=True)
            return None
        return run_id

    def _draft_note(self, question: str, answer: str, steps: list[dict[str, Any]]):
        """Ask the note-writer flow for a name, description and approach; None on failure."""
        try:
            result = asyncio.run(
                self._runner.execute(
                    flow_name=self._note_writer_flow,
                    message=build_writer_message(question, answer, format_trace(steps)),
                    session_id=f"note-writer-{uuid.uuid4().hex[:12]}",
                    user_id="note-writer",
                    interface="slack",
                )
            )
        except Exception as exc:
            print(f"[notes] note writer failed: {exc}", flush=True)
            return None
        if not result.success or result.output is None:
            print(f"[notes] note writer failed: {result.error}", flush=True)
            return None
        draft = parse_note_draft(result.output.content)
        if draft is None:
            print(f"[notes] could not parse note writer reply: {result.output.content[:300]!r}", flush=True)
        return draft

    def _take_notes(self, run_id: str | None) -> str:
        """Save the recorded run as a note; return the status line for Slack."""
        run = self._feedback_store.get_run(run_id) if self._feedback_store and run_id else None
        if not run or not run.get("question") or not run.get("answer"):
            return "There is no recorded answer here to save as a note. ⚠️"
        steps = json.loads(run.get("trace") or "[]")
        draft = self._draft_note(run["question"], run["answer"], steps)
        try:
            action, name = save_approved_note(
                run["question"],
                run["answer"],
                draft.approach if draft else tool_call_summary(steps),
                name=draft.name if draft else "",
                description=draft.description if draft else "",
            )
        except Exception as exc:
            print(f"[notes] failed to save note: {exc}", flush=True)
            return "I couldn't save this answer as a note. ⚠️"
        print(f"[notes] {action} note {name!r}", flush=True)
        return f"Saved as note `{name}`. 📝" if action == "created" else f"Updated note `{name}`. 📝"

    def _record_feedback(self, entry: dict[str, Any]) -> None:
        if self._feedback_store is not None:
            self._feedback_store.record({"timestamp": datetime.now(timezone.utc).isoformat(), **entry})

    def handle_interaction(self, request: SlackInteractionRequest) -> SlackInteractionResponse | None:
        if request.action_id not in {"feedback_up", "feedback_down", TAKE_NOTES_ACTION_ID}:
            return None
        try:
            payload = json.loads(request.action_value or "{}")
        except json.JSONDecodeError:
            payload = {}
        if request.action_id == TAKE_NOTES_ACTION_ID:
            message = request.context.get("message") or {}
            response_text = payload.get("response_text") or message.get("text", "")
            line = self._take_notes(payload.get("run_id"))
            blocks = self._blocks_after_click(message, response_text, {TAKE_NOTES_ACTION_ID}, line)
            return SlackInteractionResponse(replace_original=SlackMessagePost(response_text, blocks))
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
            blocks = self._blocks_after_click(
                message, response_text, {"feedback_up", "feedback_down"}, "Thanks for the feedback! 👍"
            )
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
        blocks = self._blocks_after_click(
            message,
            response_text,
            {"feedback_up", "feedback_down"},
            "Thanks for the feedback. Tell us more in the form if useful. ✏️",
        )
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
    """Start the Slack consulting bot (set ATHOS_SLACK_SANDBOX=1 for fixed answers)."""
    load_dotenv()
    feedback_store = FeedbackStore(Path(os.getenv("ATHOS_FEEDBACK_DB", "data/slack/feedback.db")))
    if os.getenv("ATHOS_SLACK_SANDBOX", "").strip().lower() in {"1", "true", "yes"}:
        run_socket_mode_app(create_sandbox_adapter(feedback_store))
        return
    config_path = os.getenv("ATHOS_CONFIG_PATH", "config/paper/cug_m1.yaml")
    adapter = AthosConsultingSlackAdapter(
        FlowRunner(build_config(config_path)),
        flow_name=os.getenv("ATHOS_FLOW_NAME", "cug_lang_chroma_gptoss_opt"),
        feedback_store=feedback_store,
        note_writer_flow=os.getenv("ATHOS_NOTE_WRITER_FLOW", "cug_note_writer_gptoss"),
    )
    run_socket_mode_app(adapter)


if __name__ == "__main__":
    main()
