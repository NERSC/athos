"""Shared helpers for extracting and normalizing LangGraph metrics."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)


def extract_token_usage_from_message(message: BaseMessage) -> Optional[dict]:
    """Extract token usage from a completed AI message."""
    if not isinstance(message, AIMessage):
        return None

    usage = message.usage_metadata
    if not usage:
        return None

    return {
        "input_tokens": int(usage["input_tokens"]),
        "output_tokens": int(usage["output_tokens"]),
    }


def extract_token_usage_from_chunk(chunk: BaseMessage) -> Optional[dict]:
    """Extract token usage from a streaming AI message chunk."""
    if not isinstance(chunk, AIMessageChunk):
        return None

    usage = chunk.usage_metadata
    if not usage:
        return None

    return {
        "input_tokens": int(usage["input_tokens"]),
        "output_tokens": int(usage["output_tokens"]),
    }


def aggregate_token_usage(messages: Sequence[BaseMessage]) -> Optional[dict]:
    """Sum token usage across AI messages."""
    total_input = 0
    total_output = 0

    for message in messages:
        token_usage = extract_token_usage_from_message(message)
        if not token_usage:
            continue
        total_input += token_usage["input_tokens"]
        total_output += token_usage["output_tokens"]

    if total_input or total_output:
        return {"input_tokens": total_input, "output_tokens": total_output}
    return None


def collect_tool_call_names(messages: Iterable[BaseMessage]) -> List[str]:
    """Collect tool names from AIMessage.tool_calls entries (deduped, order-preserving)."""
    names: List[str] = []
    for message in messages:
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            continue

        for tool_call in tool_calls:
            if isinstance(tool_call, Mapping) and "name" in tool_call:
                names.append(str(tool_call["name"]))

    seen = set()
    unique: List[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def current_turn_messages(messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """Return the messages after the most recent human message.

    Checkpointed graph state holds the whole thread, so this isolates the
    messages produced while answering the latest user turn.
    """
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return messages[index + 1 :]
    return messages


def _tool_result_text(content: Any) -> str:
    """Flatten ToolMessage content (string or content blocks) into text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, Mapping):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def summarize_tool_result(content: Any) -> Dict[str, Any]:
    """Summarize a tool result without including its payload.

    Reports the result size and, for JSON-object results, the ``success`` and
    ``message`` keys plus the length of every list value. Field values are
    left out so ticket contents do not end up in logs.
    """
    text = _tool_result_text(content)
    summary: Dict[str, Any] = {"chars": len(text)}
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        return summary
    if not isinstance(payload, Mapping):
        return summary
    if "success" in payload:
        summary["success"] = payload["success"]
    if isinstance(payload.get("message"), str):
        summary["message"] = payload["message"][:200]
    for key, value in payload.items():
        if isinstance(value, list):
            summary[f"{key}_count"] = len(value)
    return summary


def summarize_tool_calls(messages: Iterable[BaseMessage]) -> List[Dict[str, Any]]:
    """Pair each AIMessage tool call with its ToolMessage result summary."""
    calls: List[Dict[str, Any]] = []
    by_id: Dict[str, Dict[str, Any]] = {}
    for message in messages:
        if isinstance(message, ToolMessage):
            entry = by_id.get(message.tool_call_id)
            if entry is not None:
                entry["status"] = getattr(message, "status", None)
                entry["result"] = summarize_tool_result(message.content)
            continue
        for tool_call in getattr(message, "tool_calls", None) or []:
            if not isinstance(tool_call, Mapping) or "name" not in tool_call:
                continue
            entry = {
                "name": str(tool_call["name"]),
                "args": tool_call.get("args", {}),
                "status": None,
                "result": None,
            }
            calls.append(entry)
            if tool_call.get("id"):
                by_id[str(tool_call["id"])] = entry
    return calls
