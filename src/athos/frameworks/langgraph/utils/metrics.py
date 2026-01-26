"""Shared helpers for extracting and normalizing LangGraph metrics."""

from __future__ import annotations

from typing import Iterable, List, Mapping, Optional, Sequence

from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage


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

