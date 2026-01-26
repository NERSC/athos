"""Metrics helpers for SmolAgents results."""

from __future__ import annotations

from typing import Any, List, Mapping, Optional


def extract_token_usage_from_result(result: Any) -> Optional[dict]:
    """Extract normalized token usage from a SmolAgents result."""
    token_usage = getattr(result, "token_usage", None)
    if token_usage is None:
        return None

    if isinstance(token_usage, Mapping):
        input_tokens = token_usage.get("input_tokens")
        output_tokens = token_usage.get("output_tokens")
    else:
        input_tokens = getattr(token_usage, "input_tokens", None)
        output_tokens = getattr(token_usage, "output_tokens", None)

    if input_tokens is None or output_tokens is None:
        return None

    return {
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
    }


def extract_tool_calls_from_result(result: Any) -> List[str]:
    """Extract tool call names from a SmolAgents result."""
    names: List[str] = []
    steps = getattr(result, "steps", None)
    if not isinstance(steps, list):
        return []

    for step in steps:
        if not isinstance(step, Mapping):
            continue
        tool_calls = step.get("tool_calls")
        if not tool_calls:
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, Mapping):
                continue
            function = tool_call.get("function")
            if not isinstance(function, Mapping):
                continue
            name = function.get("name")
            if name:
                names.append(str(name))

    seen = set()
    unique: List[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique
