from __future__ import annotations

from typing import List, Set

from athos.frameworks.langgraph.flows._stream_utils import (
    build_tool_update_outputs,
)
from athos.models.flow import FlowOutput
from langchain_core.messages import AIMessage


def _build_payload_with_tool(tool_name: str) -> dict[str, List[AIMessage]]:
    message = AIMessage(
        content="",
        tool_calls=[{"id": "call-1", "name": tool_name, "args": {}}],
    )
    return {"model": [message]}


def test_build_tool_update_outputs_emits_tool_start() -> None:
    payload = _build_payload_with_tool("tavily_search")
    tool_calls_seen: List[str] = []
    seen_tool_call_ids: Set[str] = set()

    outputs = build_tool_update_outputs(
        payload,
        tool_calls_seen=tool_calls_seen,
        seen_tool_call_ids=seen_tool_call_ids,
    )

    assert len(outputs) == 1
    output: FlowOutput = outputs[0]
    assert output.metadata["event_type"] == "tool_call"
    assert output.metadata["tool_name"] == "tavily_search"
    assert "Using tool: tavily_search" in output.metadata["status_message"]
    assert tool_calls_seen == ["tavily_search"]


def test_build_tool_update_outputs_deduplicates_replayed_messages() -> None:
    payload = _build_payload_with_tool("tavily_search")
    tool_calls_seen: List[str] = []
    seen_tool_call_ids: Set[str] = {"call-1"}

    outputs = build_tool_update_outputs(
        payload,
        tool_calls_seen=tool_calls_seen,
        seen_tool_call_ids=seen_tool_call_ids,
    )

    assert outputs == []
    assert tool_calls_seen == []
