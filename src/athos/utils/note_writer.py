"""Read note activity out of an agent run, and build the note writer's input.

A front end (the Slack bot) runs flows with metadata={"debug_include_steps":
True}, so FlowOutput.metadata["langgraph_steps"] holds each run's messages
and tool calls. From those steps it learns whether the consulting agent
answered from saved notes, whether the user asked to note the thread (the
agent calls take_thread_note), and what the note-writer flow saved with
note_taker. build_thread_message turns a thread into the writer's input.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

THREAD_NOTE_TOOL = "take_thread_note"
NOTHING_TO_NOTE_MARKER = "NOTHING TO NOTE"

# note_taker's replies once it has saved, updated or kept a note.
_NOTE_SAVED_RES = (
    ("created", re.compile(r"^Saved as note '([^']+)'")),
    ("updated", re.compile(r"^Updated note '([^']+)'")),
    ("unchanged", re.compile(r"^No changes made; note '([^']+)'")),
)


def turn_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep only the latest turn: the steps after the last human message.

    The flow's checkpoint holds the whole thread, so earlier turns in the
    same Slack thread show up in the steps too.
    """

    last_human = max(
        (i for i, step in enumerate(steps) if step.get("role") == "human"), default=-1
    )
    return steps[last_human + 1 :]


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        ]
        return "\n".join(p for p in parts if p)
    return "" if content is None else json.dumps(content, default=str)


def _tool_calls(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        call
        for step in steps
        if step.get("role") == "ai"
        for call in step.get("tool_calls") or []
    ]


_NOTE_LOOKUP_TOOLS = {"list_notes", "read_note"}


def notes_answered_from(steps: List[Dict[str, Any]]) -> List[str]:
    """Names of the notes one turn's answer came from, or [] if it did not.

    An answer counts as from notes when read_note loaded at least one note and
    the agent made no other tool call, i.e. it did not fall back to retrieval.
    """

    note_args: Dict[str, str] = {}
    for call in _tool_calls(steps):
        if call.get("name") not in _NOTE_LOOKUP_TOOLS:
            return []
        if call.get("name") == "read_note":
            note_args[call.get("id") or ""] = str((call.get("args") or {}).get("name", ""))

    names: List[str] = []
    for step in steps:
        if step.get("role") != "tool" or step.get("name") != "read_note":
            continue
        name = note_args.get(step.get("tool_call_id") or "", "")
        # read_note answers "No note named ..." when the note does not exist.
        if name and not _text(step.get("content")).startswith("No note named") and name not in names:
            names.append(name)
    return names


def thread_note_requested(steps: List[Dict[str, Any]]) -> bool:
    """Whether the agent called take_thread_note in this turn."""

    return any(call.get("name") == THREAD_NOTE_TOOL for call in _tool_calls(steps))


def build_thread_message(transcript: Sequence[Tuple[str, str]]) -> str:
    """Render (speaker, text) pairs, oldest first, as the note writer's input."""

    lines = [f"[{index}] {speaker}:\n{text.strip()}" for index, (speaker, text) in enumerate(transcript, 1)]
    return "SLACK THREAD (oldest message first)\n\n" + "\n\n".join(lines)


def note_saved(
    steps: List[Dict[str, Any]],
) -> Optional[Tuple[Literal["created", "updated", "unchanged"], str]]:
    """The last note note_taker created, updated or kept, as (action, name); None if none."""

    saved = None
    for step in steps:
        if step.get("role") != "tool" or step.get("name") != "note_taker":
            continue
        content = _text(step.get("content"))
        for action, pattern in _NOTE_SAVED_RES:
            match = pattern.match(content)
            if match:
                saved = (action, match.group(1))
                break
    return saved
