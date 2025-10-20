"""Tests for LangGraph translation utilities."""

from __future__ import annotations

import pytest

from langchain_core.messages import BaseMessage

from athos.frameworks.langgraph.utils.translation import (
    build_langgraph_config,
    from_langgraph_messages,
    to_langgraph_messages,
)
from athos.frameworks.langgraph.utils.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


class _UnknownMessage(BaseMessage):
    """Simple message subclass used to ensure unknown types are ignored."""

    type: str = "unknown"

    def __init__(self, content: str) -> None:  # pragma: no cover - trivial init
        super().__init__(content=content)


class TestToLanggraphMessages:
    """Unit tests for to_langgraph_messages utility."""

    def test_converts_basic_roles(self) -> None:
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "system", "content": "You are helpful"},
        ]

        result = to_langgraph_messages(messages)

        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert isinstance(result[2], SystemMessage)
        assert [msg.content for msg in result] == [
            "Hello",
            "Hi there",
            "You are helpful",
        ]

    def test_preserves_metadata_and_ids(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": "Working on it",
                "id": "123",
                "metadata": {"model": "gpt"},
                "additional_kwargs": {"foo": "bar"},
                "tool_calls": ["call"],
                "response_metadata": {"latency_ms": 12},
            }
        ]

        result = to_langgraph_messages(messages)

        ai_message = result[0]
        assert isinstance(ai_message, AIMessage)
        assert ai_message.id == "123"
        assert ai_message.metadata == {"model": "gpt"}
        assert ai_message.additional_kwargs["foo"] == "bar"
        assert ai_message.additional_kwargs["tool_calls"] == ["call"]
        assert ai_message.response_metadata == {"latency_ms": 12}

    def test_skips_unknown_roles(self) -> None:
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "custom", "content": "Ignore me"},
            {"role": "assistant", "content": "Hi"},
        ]

        result = to_langgraph_messages(messages)

        assert len(result) == 2
        assert all(isinstance(msg, (HumanMessage, AIMessage)) for msg in result)

    def test_raises_on_non_mapping(self) -> None:
        with pytest.raises(TypeError):
            to_langgraph_messages(["bad payload"])  # type: ignore[list-item]


class TestFromLanggraphMessages:
    """Unit tests for from_langgraph_messages utility."""

    def test_converts_basic_messages(self) -> None:
        messages = [
            HumanMessage("Hi"),
            AIMessage("Hello"),
            SystemMessage("You are helpful"),
            ToolMessage("42", name="calculator", tool_call_id="abc"),
        ]

        result = from_langgraph_messages(messages)

        assert result == [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
            {"role": "system", "content": "You are helpful"},
            {
                "role": "tool",
                "content": "42",
                "name": "calculator",
                "tool_call_id": "abc",
            },
        ]

    def test_preserves_metadata_and_additional_fields(self) -> None:
        message = AIMessage(
            content="Done",
            additional_kwargs={"foo": "bar"},
            metadata={"model": "gpt"},
            id="xyz",
        )
        message.response_metadata = {"latency_ms": 10}  # type: ignore[attr-defined]

        result = from_langgraph_messages([message])

        assert result == [
            {
                "role": "assistant",
                "content": "Done",
                "additional_kwargs": {"foo": "bar"},
                "metadata": {"model": "gpt"},
                "id": "xyz",
                "response_metadata": {"latency_ms": 10},
            }
        ]

    def test_ignores_unknown_message_types(self) -> None:
        result = from_langgraph_messages([_UnknownMessage("ignored")])
        assert result == []

    def test_handles_empty_iterable(self) -> None:
        assert from_langgraph_messages([]) == []
        assert from_langgraph_messages(None) == []  # type: ignore[arg-type]


class TestBuildLanggraphConfig:
    """Tests for build_langgraph_config utility."""

    def test_builds_default_config(self) -> None:
        config = build_langgraph_config("session-123")
        assert config == {"configurable": {"thread_id": "session-123"}}

    def test_merges_langgraph_config(self) -> None:
        metadata = {
            "langgraph_config": {
                "configurable": {"checkpoint_ns": "demo"},
                "tags": ["test"],
            }
        }

        config = build_langgraph_config("session-abc", metadata)

        assert config["configurable"]["thread_id"] == "session-abc"
        assert config["configurable"]["checkpoint_ns"] == "demo"
        assert config["tags"] == ["test"]

    def test_ignores_invalid_metadata(self) -> None:
        config = build_langgraph_config("session-xyz", {"langgraph_config": "not-a-dict"})
        assert config == {"configurable": {"thread_id": "session-xyz"}}
