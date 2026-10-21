"""Turn an agent run into the material for a note's Approach section.

A front end (the Slack bot) keeps each answered run's question, answer and
LangGraph steps (from FlowOutput.metadata["langgraph_steps"], produced when
a flow runs with metadata={"debug_include_steps": True}). When a user asks
to keep the answer as a note, it formats the run with build_writer_message,
sends that to a no-tools note-writer flow, and reads the reply with
parse_note_draft.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_RESULT_MAX = 1500
_TRACE_MAX = 12000

_FIELD_RE = re.compile(r"^\W*(name|description|approach)\W*:[ \t]*(.*)$", re.IGNORECASE)


@dataclass
class NoteDraft:
    name: str
    description: str
    approach: str


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


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else f"{text[:limit]} ...[cut {len(text) - limit} chars]"


def format_trace(steps: List[Dict[str, Any]]) -> str:
    """Render one turn's steps as numbered tool calls and their results."""

    lines: List[str] = []
    for step in steps:
        role = step.get("role")
        if role == "ai":
            for call in step.get("tool_calls") or []:
                args = json.dumps(call.get("args", {}), default=str)
                lines.append(f"CALL {call.get('name')}({args})")
        elif role == "tool":
            result = _clip(_text(step.get("content")), _RESULT_MAX)
            lines.append(f"RESULT of {step.get('name')}:\n{result}")
    if not lines:
        return "(no tool calls: the answer was written without any lookups)"
    trace = "\n\n".join(lines)
    return _clip(trace, _TRACE_MAX)


def tool_call_summary(steps: List[Dict[str, Any]]) -> str:
    """Fallback approach when no note-writer reply is available."""

    calls = [
        f"- {call.get('name')}({json.dumps(call.get('args', {}), default=str)})"
        for step in steps
        if step.get("role") == "ai"
        for call in step.get("tool_calls") or []
    ]
    if not calls:
        return "Answered without any tool lookups."
    return "Tool calls made while answering, in order:\n" + "\n".join(calls)


def build_writer_message(question: str, answer: str, trace: str) -> str:
    return (
        f"QUESTION\n{question.strip()}\n\n"
        f"FINAL ANSWER\n{answer.strip()}\n\n"
        f"TRACE (tool calls and results, in order)\n{trace}"
    )


def parse_note_draft(text: str) -> Optional[NoteDraft]:
    """Read NAME / DESCRIPTION / APPROACH from the note writer's reply."""

    fields: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for line in text.strip().splitlines():
        match = _FIELD_RE.match(line)
        if match and match.group(1).lower() not in fields:
            current = match.group(1).lower()
            fields[current] = [match.group(2)]
        elif current:
            fields[current].append(line)

    def get(key: str) -> str:
        return "\n".join(fields.get(key, [])).strip().strip("*`").strip()

    name, description, approach = get("name"), get("description"), get("approach")
    if not approach:
        return None
    return NoteDraft(name=name, description=" ".join(description.split()), approach=approach)
