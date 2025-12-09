"""Shared helpers for extracting and normalizing LangGraph metrics."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Optional, Sequence

from langchain_core.messages import AIMessage, BaseMessage


def aggregate_token_usage(messages: Sequence[BaseMessage]) -> Optional[dict]:
    """Sum token usage across AI messages.

    Supports LangChain `usage_metadata` and `response_metadata.token_usage/usage`.
    Returns a dict with input_tokens/output_tokens when any usage is found.
    """
    total_input = 0
    total_output = 0

    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        usage = getattr(message, "usage_metadata", None) or getattr(message, "response_metadata", None)
        token_usage = _coerce_usage(usage)
        if token_usage:
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
            elif hasattr(tool_call, "name"):
                names.append(str(getattr(tool_call, "name")))

    seen = set()
    unique: List[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def _coerce_usage(usage: Any) -> Optional[dict]:
    """Normalize usage payloads to a token_usage dict."""

    token_usage: Any
    if isinstance(usage, Mapping):
        token_usage = usage.get("token_usage") or usage.get("usage") or usage
    else:
        token_usage = getattr(usage, "token_usage", None) or getattr(usage, "usage", None)

    if not isinstance(token_usage, Mapping):
        return None

    input_tokens = token_usage.get("input_tokens", 0)
    output_tokens = token_usage.get("output_tokens", 0)

    try:
        input_tokens = int(input_tokens)
        output_tokens = int(output_tokens)
    except (TypeError, ValueError):
        return None

    if input_tokens == 0 and output_tokens == 0:
        return None

    return {"input_tokens": input_tokens, "output_tokens": output_tokens}
