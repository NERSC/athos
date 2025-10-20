"""Translation utilities between ATHOS and LangGraph formats."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

_VALID_ROLES = {"user", "assistant", "system", "tool"}


def _extract_common_message_kwargs(message: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract shared keyword arguments when creating LangChain messages."""

    kwargs: Dict[str, Any] = {}

    additional_kwargs = message.get("additional_kwargs")
    if isinstance(additional_kwargs, Mapping):
        kwargs["additional_kwargs"] = dict(additional_kwargs)

    metadata = message.get("metadata")
    if isinstance(metadata, Mapping):
        kwargs["metadata"] = dict(metadata)

    if "id" in message:
        kwargs["id"] = message["id"]

    return kwargs


def to_langgraph_messages(session_messages: Optional[Iterable[Mapping[str, Any]]]) -> List[BaseMessage]:
    """Convert ATHOS session messages to LangGraph message objects."""

    if not session_messages:
        return []

    converted: List[BaseMessage] = []
    for raw in session_messages:
        if not isinstance(raw, Mapping):
            raise TypeError(
                "Session messages must be mapping objects with role/content entries."
            )

        role = str(raw.get("role", "")).lower()
        if role not in _VALID_ROLES:
            # Skip entries with roles we do not understand. This keeps translation
            # resilient to experimental message types without failing flows.
            continue

        content = raw.get("content", "")
        kwargs = _extract_common_message_kwargs(raw)

        if role == "user":
            converted.append(HumanMessage(content=content, **kwargs))
        elif role == "assistant":
            ai_kwargs = dict(kwargs)
            # Preserve tool call metadata if present
            tool_calls = raw.get("tool_calls")
            if tool_calls is not None:
                ai_kwargs.setdefault("additional_kwargs", {})
                ai_kwargs["additional_kwargs"]["tool_calls"] = tool_calls

            response_metadata = raw.get("response_metadata")
            if isinstance(response_metadata, Mapping):
                ai_kwargs["response_metadata"] = dict(response_metadata)

            converted.append(AIMessage(content=content, **ai_kwargs))
        elif role == "system":
            converted.append(SystemMessage(content=content, **kwargs))
        else:  # role == "tool"
            converted.append(
                ToolMessage(
                    content,
                    name=raw.get("name"),
                    tool_call_id=raw.get("tool_call_id"),
                    **kwargs,
                )
            )

    return converted


def from_langgraph_messages(messages: Optional[Iterable[BaseMessage]]) -> List[Dict[str, Any]]:
    """Convert LangGraph messages to ATHOS session message dictionaries."""

    if not messages:
        return []

    converted: List[Dict[str, Any]] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            entry: Dict[str, Any] = {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            entry = {"role": "assistant", "content": message.content}

            if getattr(message, "additional_kwargs", None):
                entry["additional_kwargs"] = dict(message.additional_kwargs)

            if getattr(message, "tool_calls", None):
                entry["tool_calls"] = message.tool_calls

            if getattr(message, "response_metadata", None):
                entry["response_metadata"] = dict(message.response_metadata)
        elif isinstance(message, SystemMessage):
            entry = {"role": "system", "content": message.content}
        elif isinstance(message, ToolMessage):
            entry = {
                "role": "tool",
                "content": message.content,
                "name": message.name,
                "tool_call_id": message.tool_call_id,
            }
        else:
            # Unknown message types are ignored to keep translation robust
            continue

        if getattr(message, "metadata", None):
            entry["metadata"] = dict(message.metadata)

        if getattr(message, "additional_kwargs", None) and "additional_kwargs" not in entry:
            entry["additional_kwargs"] = dict(message.additional_kwargs)

        if getattr(message, "id", None):
            entry["id"] = message.id

        converted.append(entry)

    return converted


def build_langgraph_config(session_id: str, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Build LangGraph configuration dictionary using ATHOS session data."""

    base_config: Dict[str, Any] = {
        "configurable": {
            "thread_id": session_id,
        }
    }

    if metadata is None:
        return base_config

    langgraph_config = metadata.get("langgraph_config")
    if isinstance(langgraph_config, Mapping):
        # Merge dictionaries while preserving base configuration precedence.
        merged = dict(langgraph_config)
        configurable = dict(base_config["configurable"])
        if isinstance(merged.get("configurable"), Mapping):
            configurable.update(dict(merged["configurable"]))
        merged["configurable"] = configurable
        base_config.update(merged)

    return base_config
