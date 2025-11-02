"""Utilities for working with LangGraph streaming responses.

These helpers centralize the logic for interpreting the output of
``CompiledStateGraph.astream`` when using ``stream_mode``. They provide
utilities that:

* Convert message chunks into plain text for incremental token streaming.
* Interpret ``"updates"`` payloads to emit structured :class:`FlowOutput`
  instances describing tool usage.

The functions are shared across the LangGraph agent-style flows to avoid
duplicating the fairly nuanced parsing logic.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, MutableSequence, Sequence, Set, Tuple

from athos.models.flow import FlowOutput
from langchain_core.messages import AIMessage, BaseMessage


def coerce_stream_chunk_text(chunk: object) -> str:
    """Best-effort conversion of streaming chunks into textual content.

    LangGraph/ LangChain streaming chunks can surface text in several shapes
    depending on the configured ``output_version`` and model backend. This
    function mirrors the heuristics used by the chatbot flow to extract the
    incremental text while gracefully ignoring unfamiliar payloads.
    """

    if chunk is None:
        return ""

    if isinstance(chunk, str):
        return chunk

    # LangChain ``AIMessageChunk`` exposes text via ``content`` or ``text``.
    content = getattr(chunk, "content", None)
    if isinstance(content, str) and content:
        return content

    if isinstance(content, Iterable) and not isinstance(content, (str, bytes)):
        pieces: List[str] = []
        for item in content:
            if isinstance(item, Mapping):
                text = item.get("text")
                if isinstance(text, str):
                    pieces.append(text)
        if pieces:
            return "".join(pieces)

    text = getattr(chunk, "text", None)
    if isinstance(text, str) and text:
        return text

    delta = getattr(chunk, "delta", None)
    if isinstance(delta, str) and delta:
        return delta

    if hasattr(delta, "content"):
        delta_content = getattr(delta, "content")
        if isinstance(delta_content, str) and delta_content:
            return delta_content
        if isinstance(delta_content, Iterable) and not isinstance(
            delta_content, (str, bytes)
        ):
            pieces = [
                item.get("text")
                for item in delta_content
                if isinstance(item, Mapping) and isinstance(item.get("text"), str)
            ]
            if pieces:
                return "".join(pieces)

    # For unknown chunk shapes we omit emitting data rather than showing noisy
    # ``repr`` strings in the UI. Callers treat empty strings as "no chunk".
    return ""


def build_tool_update_outputs(
    updates: Any,
    *,
    tool_calls_seen: MutableSequence[str],
    seen_tool_call_ids: Set[str],
) -> List[FlowOutput]:
    """Convert ``stream_mode="updates"`` payloads into ``FlowOutput`` objects.

    Parameters
    ----------
    updates:
        Raw payload emitted by ``CompiledStateGraph.astream`` for the
        ``"updates"`` stream mode. Typically a mapping of node name ->
        list of :class:`~langchain_core.messages.BaseMessage` instances.
    tool_calls_seen:
        Mutable sequence tracking the human-readable names of the tools that
        have been announced. The sequence is appended to whenever a new tool
        invocation is detected so that callers can include it in their final
        metadata payloads.
    seen_tool_call_ids:
        Set of synthetic identifiers used to de-duplicate tool call
        notifications. LangGraph replays the latest state on every update, so
        without de-duplication we would emit the same status repeatedly.

    Returns
    -------
    list[FlowOutput]
        ``FlowOutput`` instances describing tool invocation events derived from
        the update payload.
    """

    outputs: List[FlowOutput] = []

    if not isinstance(updates, Mapping):
        return outputs

    for node_name, node_payload in updates.items():
        node = str(node_name)
        for message in _coerce_update_messages(node_payload):
            outputs.extend(
                _build_outputs_for_message(
                    message,
                    node=node,
                    tool_calls_seen=tool_calls_seen,
                    seen_tool_call_ids=seen_tool_call_ids,
                )
            )

    return outputs


def _coerce_update_messages(payload: Any) -> Sequence[BaseMessage]:
    """Normalize update payloads into an iterable of messages."""

    if isinstance(payload, BaseMessage):
        return [payload]

    if isinstance(payload, Mapping):
        candidate = payload.get("messages")
        if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes)):
            return [msg for msg in candidate if isinstance(msg, BaseMessage)]
        return []

    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        return [msg for msg in payload if isinstance(msg, BaseMessage)]

    return []


def _build_outputs_for_message(
    message: BaseMessage,
    *,
    node: str,
    tool_calls_seen: MutableSequence[str],
    seen_tool_call_ids: Set[str],
) -> List[FlowOutput]:
    outputs: List[FlowOutput] = []

    if isinstance(message, AIMessage):
        for dedup_id, display_name, public_id in _iter_tool_calls(message):
            if dedup_id in seen_tool_call_ids:
                continue
            seen_tool_call_ids.add(dedup_id)
            tool_calls_seen.append(display_name)
            metadata = {
                "streaming": True,
                "event_type": "tool_call",
                "tool_name": display_name,
                "tool_call_id": public_id,
                "status_message": f"🔧 Using tool: {display_name}\n\n",
                "node": node,
            }
            outputs.append(FlowOutput(content="", metadata=metadata))

    return outputs


def _iter_tool_calls(message: AIMessage) -> Iterable[Tuple[str, str, str | None]]:
    """Yield de-duplicated tool call information from an AI message."""

    tool_calls = getattr(message, "tool_calls", None)
    if not tool_calls:
        return []

    extracted: List[Tuple[str, str, str | None]] = []
    for entry in tool_calls:
        call_id: str | None = None
        name: str | None = None

        if isinstance(entry, Mapping):
            raw_id = entry.get("id") or entry.get("tool_call_id")
            if isinstance(raw_id, str):
                call_id = raw_id
            func = entry.get("function")
            if isinstance(func, Mapping):
                func_name = func.get("name")
                if isinstance(func_name, str):
                    name = func_name
            raw_name = entry.get("name")
            if isinstance(raw_name, str):
                name = raw_name
        else:
            call_id = getattr(entry, "id", None) or getattr(entry, "tool_call_id", None)
            name = getattr(entry, "name", None)
            function = getattr(entry, "function", None)
            if not name and function is not None:
                name = getattr(function, "name", None)

        display_name = name or "unknown_tool"
        dedup_id = call_id if call_id is not None else f"{display_name}:{id(entry)}"
        extracted.append((dedup_id, display_name, call_id))

    return extracted


__all__ = [
    "coerce_stream_chunk_text",
    "build_tool_update_outputs",
]
