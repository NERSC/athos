"""Utilities for working with LangChain message objects.

This module provides helper functions for converting various message formats
into LangChain message objects, enabling flexible input handling across
LangGraph flows.

Note: langchain-core is a required dependency for ATHOS, so these imports
will always succeed.
"""

from __future__ import annotations

from typing import Any, Iterable, List

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


def coerce_to_messages(messages: Any) -> List["BaseMessage"]:
    """Convert various message payloads into LangChain message objects.

    This function provides flexible input handling, accepting messages in
    multiple formats and normalizing them to LangChain BaseMessage instances.

    Args:
        messages: Message(s) in various formats, which can be:
            - None (returns empty list)
            - Single BaseMessage instance
            - Single string (converted to HumanMessage)
            - Single dict with role/content keys
            - List/iterable of any of the above

    Returns:
        List of LangChain BaseMessage objects

    Raises:
        TypeError: If a message format is not recognized

    Examples:
        >>> coerce_to_messages(None)
        []

        >>> coerce_to_messages("Hello")
        [HumanMessage(content='Hello')]

        >>> coerce_to_messages({"role": "user", "content": "Hi"})
        [HumanMessage(content='Hi')]

        >>> coerce_to_messages([
        ...     {"role": "user", "content": "What is NERSC?"},
        ...     {"role": "assistant", "content": "NERSC is..."}
        ... ])
        [HumanMessage(content='What is NERSC?'), AIMessage(content='NERSC is...')]
    """
    if messages is None:
        return []

    if isinstance(messages, dict):
        items = [messages]
    elif isinstance(messages, Iterable) and not isinstance(messages, (str, bytes)):
        items = list(messages)
    else:
        items = [messages]

    converted: List["BaseMessage"] = []
    for item in items:
        converted.append(coerce_single_message(item))
    return converted


def coerce_single_message(message: Any) -> "BaseMessage":
    """Coerce a single message entry into a LangChain message instance.

    Args:
        message: Single message in one of the following formats:
            - BaseMessage instance (returned as-is)
            - String (converted to HumanMessage)
            - Dict with "role"/"type" and "content" keys

    Returns:
        LangChain BaseMessage instance

    Raises:
        TypeError: If message format is not recognized

    Examples:
        >>> coerce_single_message("Hello")
        HumanMessage(content='Hello')

        >>> coerce_single_message({"role": "assistant", "content": "Hi there"})
        AIMessage(content='Hi there')

        >>> coerce_single_message({"type": "system", "content": "You are helpful"})
        SystemMessage(content='You are helpful')

        >>> coerce_single_message({
        ...     "role": "tool",
        ...     "content": "Result",
        ...     "name": "search",
        ...     "tool_call_id": "123"
        ... })
        ToolMessage(content='Result', name='search', tool_call_id='123')
    """
    if isinstance(message, BaseMessage):
        return message

    if isinstance(message, str):
        return HumanMessage(message)

    if isinstance(message, dict):
        role = (message.get("role") or message.get("type") or "").lower()
        content = message.get("content", "")

        if role in {"user", "human"}:
            return HumanMessage(content)
        if role in {"assistant", "ai"}:
            return AIMessage(content)
        if role == "system":
            return SystemMessage(content)
        if role == "tool":
            return ToolMessage(
                content,
                name=message.get("name"),
                tool_call_id=message.get("tool_call_id"),
            )

    raise TypeError(
        f"Unsupported message payload: {type(message)!r}. "
        f"Expected BaseMessage, str, or dict with role/content keys."
    )
