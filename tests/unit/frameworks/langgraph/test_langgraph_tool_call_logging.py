"""Tests for per-turn tool-call summaries used in LangGraph flow logging."""

import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from athos.frameworks.langgraph.flows import agent as agent_module
from athos.frameworks.langgraph.flows.agent import LangChainAgentFlow
from athos.frameworks.langgraph.utils.metrics import (
    current_turn_messages,
    summarize_tool_calls,
    summarize_tool_result,
)

pytestmark = pytest.mark.unit


def _tool_turn(call_id, name, args, result):
    return [
        AIMessage(content="", tool_calls=[{"id": call_id, "name": name, "args": args}]),
        ToolMessage(content=result, tool_call_id=call_id, name=name),
    ]


def test_current_turn_messages_returns_messages_after_last_human():
    old = _tool_turn("a", "list_incidents", {}, "{}")
    new = _tool_turn("b", "list_incidents", {"incident_number": "INC1"}, "{}")
    messages = [HumanMessage(content="q1"), *old, AIMessage(content="a1"), HumanMessage(content="q2"), *new]

    assert list(current_turn_messages(messages)) == new


def test_current_turn_messages_without_human_returns_all():
    messages = [AIMessage(content="hi")]
    assert list(current_turn_messages(messages)) == messages


def test_summarize_tool_result_reports_counts_not_payload():
    payload = {
        "success": True,
        "message": "Found 0 log entries",
        "logs": [],
        "incidents": [{"comments_and_work_notes": "secret ticket text"}],
    }
    summary = summarize_tool_result(json.dumps(payload))

    assert summary["success"] is True
    assert summary["message"] == "Found 0 log entries"
    assert summary["logs_count"] == 0
    assert summary["incidents_count"] == 1
    assert "secret ticket text" not in json.dumps(summary)


def test_summarize_tool_result_handles_content_blocks_and_non_json():
    blocks = [{"type": "text", "text": json.dumps({"success": False, "items": [1, 2]})}]
    assert summarize_tool_result(blocks) == {"chars": len(blocks[0]["text"]), "success": False, "items_count": 2}
    assert summarize_tool_result("plain text") == {"chars": 10}


def test_summarize_tool_calls_pairs_calls_with_results():
    args = {"incident_number": "INC0266281", "include_comments_and_work_notes": True}
    messages = _tool_turn("c1", "list_incidents", args, json.dumps({"success": True, "incidents": [{}]}))

    calls = summarize_tool_calls(messages)

    assert len(calls) == 1
    assert calls[0]["name"] == "list_incidents"
    assert calls[0]["args"] == args
    assert calls[0]["result"]["incidents_count"] == 1


def test_log_tool_calls_logs_only_latest_turn(monkeypatch):
    flow = LangChainAgentFlow.__new__(LangChainAgentFlow)
    state = {
        "messages": [
            HumanMessage(content="q1"),
            *_tool_turn("a", "view_incident_logs", {"incident_number": "INC1"}, "{}"),
            AIMessage(content="a1"),
            HumanMessage(content="q2"),
            *_tool_turn("b", "list_incidents", {"incident_number": "INC2"}, '{"success": true}'),
            AIMessage(content="a2"),
        ]
    }

    # Patch the module logger directly: other tests reconfigure athos logging
    # (e.g. disable propagation), which makes caplog unreliable here.
    lines = []
    monkeypatch.setattr(agent_module.logger, "info", lambda msg, *args: lines.append(msg % args))

    flow._log_tool_calls(state)

    lines = [line for line in lines if line.startswith("Tool call:")]
    assert len(lines) == 1
    assert "name=list_incidents" in lines[0]
    assert "INC2" in lines[0]
    assert '"success": true' in lines[0]
