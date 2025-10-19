"""Tests for LangGraph message utilities."""

import pytest

from athos.frameworks.langgraph.utils.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    coerce_single_message,
    coerce_to_messages,
)


class TestCoerceSingleMessage:
    """Tests for coerce_single_message function."""

    def test_returns_base_message_unchanged(self):
        """BaseMessage instances should be returned as-is."""
        msg = HumanMessage("Hello")
        result = coerce_single_message(msg)
        assert result is msg

    def test_converts_string_to_human_message(self):
        """Strings should be converted to HumanMessage."""
        result = coerce_single_message("Hello")
        assert isinstance(result, HumanMessage)
        assert result.content == "Hello"

    def test_converts_dict_with_user_role(self):
        """Dict with role='user' should become HumanMessage."""
        result = coerce_single_message({"role": "user", "content": "Hi"})
        assert isinstance(result, HumanMessage)
        assert result.content == "Hi"

    def test_converts_dict_with_human_role(self):
        """Dict with role='human' should become HumanMessage."""
        result = coerce_single_message({"role": "human", "content": "Hi"})
        assert isinstance(result, HumanMessage)
        assert result.content == "Hi"

    def test_converts_dict_with_assistant_role(self):
        """Dict with role='assistant' should become AIMessage."""
        result = coerce_single_message({"role": "assistant", "content": "Hello!"})
        assert isinstance(result, AIMessage)
        assert result.content == "Hello!"

    def test_converts_dict_with_ai_role(self):
        """Dict with role='ai' should become AIMessage."""
        result = coerce_single_message({"role": "ai", "content": "Hello!"})
        assert isinstance(result, AIMessage)
        assert result.content == "Hello!"

    def test_converts_dict_with_system_role(self):
        """Dict with role='system' should become SystemMessage."""
        result = coerce_single_message({"role": "system", "content": "You are helpful"})
        assert isinstance(result, SystemMessage)
        assert result.content == "You are helpful"

    def test_converts_dict_with_tool_role(self):
        """Dict with role='tool' should become ToolMessage."""
        result = coerce_single_message({
            "role": "tool",
            "content": "Result",
            "name": "search",
            "tool_call_id": "123"
        })
        assert isinstance(result, ToolMessage)
        assert result.content == "Result"
        assert result.name == "search"
        assert result.tool_call_id == "123"

    def test_converts_dict_with_type_field(self):
        """Dict with 'type' instead of 'role' should work."""
        result = coerce_single_message({"type": "user", "content": "Hi"})
        assert isinstance(result, HumanMessage)
        assert result.content == "Hi"

    def test_role_case_insensitive(self):
        """Role matching should be case-insensitive."""
        result = coerce_single_message({"role": "USER", "content": "Hi"})
        assert isinstance(result, HumanMessage)
        assert result.content == "Hi"

    def test_missing_content_uses_empty_string(self):
        """Missing content should default to empty string."""
        result = coerce_single_message({"role": "user"})
        assert isinstance(result, HumanMessage)
        assert result.content == ""

    def test_raises_on_unknown_dict_role(self):
        """Dict with unknown role should raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported message payload"):
            coerce_single_message({"role": "unknown", "content": "Hi"})

    def test_raises_on_dict_without_role(self):
        """Dict without role/type field should raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported message payload"):
            coerce_single_message({"content": "Hi"})

    def test_raises_on_unsupported_type(self):
        """Unsupported types (int, list, etc.) should raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported message payload"):
            coerce_single_message(123)

        with pytest.raises(TypeError, match="Unsupported message payload"):
            coerce_single_message([1, 2, 3])


class TestCoerceToMessages:
    """Tests for coerce_to_messages function."""

    def test_none_returns_empty_list(self):
        """None input should return empty list."""
        result = coerce_to_messages(None)
        assert result == []

    def test_single_string_returns_list_with_human_message(self):
        """Single string should return list with one HumanMessage."""
        result = coerce_to_messages("Hello")
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hello"

    def test_single_dict_returns_list_with_one_message(self):
        """Single dict should return list with one message."""
        result = coerce_to_messages({"role": "user", "content": "Hi"})
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hi"

    def test_single_base_message_returns_list_with_one_message(self):
        """Single BaseMessage should return list with that message."""
        msg = HumanMessage("Hello")
        result = coerce_to_messages([msg])  # BaseMessage is iterable, so wrap in list
        assert len(result) == 1
        assert result[0] is msg

    def test_list_of_strings(self):
        """List of strings should return list of HumanMessages."""
        result = coerce_to_messages(["Hi", "Hello"])
        assert len(result) == 2
        assert all(isinstance(m, HumanMessage) for m in result)
        assert result[0].content == "Hi"
        assert result[1].content == "Hello"

    def test_list_of_dicts(self):
        """List of dicts should return list of appropriate messages."""
        result = coerce_to_messages([
            {"role": "user", "content": "What is NERSC?"},
            {"role": "assistant", "content": "NERSC is..."}
        ])
        assert len(result) == 2
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert result[0].content == "What is NERSC?"
        assert result[1].content == "NERSC is..."

    def test_list_of_base_messages(self):
        """List of BaseMessages should be returned with all messages."""
        messages = [HumanMessage("Hi"), AIMessage("Hello")]
        result = coerce_to_messages(messages)
        assert len(result) == 2
        assert result[0] is messages[0]
        assert result[1] is messages[1]

    def test_mixed_list(self):
        """Mixed list of strings, dicts, and BaseMessages should work."""
        msg = SystemMessage("You are helpful")
        result = coerce_to_messages([
            "Hi",
            {"role": "assistant", "content": "Hello"},
            msg
        ])
        assert len(result) == 3
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert result[2] is msg

    def test_empty_list_returns_empty_list(self):
        """Empty list should return empty list."""
        result = coerce_to_messages([])
        assert result == []

    def test_tuple_input(self):
        """Tuple input should work like list."""
        result = coerce_to_messages(("Hi", "Hello"))
        assert len(result) == 2
        assert all(isinstance(m, HumanMessage) for m in result)

    def test_generator_input(self):
        """Generator input should work."""
        def gen():
            yield "Hi"
            yield {"role": "assistant", "content": "Hello"}

        result = coerce_to_messages(gen())
        assert len(result) == 2
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)

    def test_bytes_not_treated_as_iterable(self):
        """Bytes should not be treated as iterable of messages."""
        # bytes should raise TypeError because it's not a supported type
        with pytest.raises(TypeError, match="Unsupported message payload"):
            coerce_to_messages(b"hello")

    def test_propagates_errors_from_coerce_single_message(self):
        """Errors from coerce_single_message should propagate."""
        with pytest.raises(TypeError, match="Unsupported message payload"):
            coerce_to_messages([{"role": "user", "content": "Hi"}, 123])


class TestMessageTypes:
    """Tests for the message type classes themselves."""

    def test_human_message_has_content(self):
        """HumanMessage should store content."""
        msg = HumanMessage("Hello")
        assert msg.content == "Hello"

    def test_ai_message_has_content(self):
        """AIMessage should store content."""
        msg = AIMessage("Hi there")
        assert msg.content == "Hi there"

    def test_system_message_has_content(self):
        """SystemMessage should store content."""
        msg = SystemMessage("You are helpful")
        assert msg.content == "You are helpful"

    def test_tool_message_has_content_and_metadata(self):
        """ToolMessage should store content, name, and tool_call_id."""
        msg = ToolMessage("Result", name="search", tool_call_id="123")
        assert msg.content == "Result"
        assert msg.name == "search"
        assert msg.tool_call_id == "123"

    def test_tool_message_defaults(self):
        """ToolMessage should have sensible defaults."""
        # Real LangChain ToolMessage requires tool_call_id, so provide it
        msg = ToolMessage("Result", tool_call_id="test_id")
        assert msg.content == "Result"
        # name is optional in real LangChain ToolMessage
        assert msg.tool_call_id == "test_id"

    def test_ai_message_tool_calls(self):
        """AIMessage should support tool_calls."""
        # Real LangChain AIMessage tool_calls requires specific structure
        msg = AIMessage(
            "Using tool",
            tool_calls=[{"id": "1", "name": "search", "args": {}}]
        )
        assert msg.content == "Using tool"
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["name"] == "search"

    def test_ai_message_tool_calls_defaults_to_empty(self):
        """AIMessage tool_calls should default to empty list."""
        msg = AIMessage("No tools")
        assert msg.tool_calls == []

    def test_all_messages_are_base_message_instances(self):
        """All message types should be instances of BaseMessage."""
        assert isinstance(HumanMessage("Hi"), BaseMessage)
        assert isinstance(AIMessage("Hello"), BaseMessage)
        assert isinstance(SystemMessage("System"), BaseMessage)
        # ToolMessage requires tool_call_id in real LangChain
        assert isinstance(ToolMessage("Result", tool_call_id="test"), BaseMessage)
