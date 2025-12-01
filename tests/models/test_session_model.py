from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from athos.models import FlowSession


def test_session_add_user_message_updates_history_and_timestamp():
    """Test that adding user messages updates history and timestamp."""
    session = FlowSession(session_id="sess-3", user_id="user-3")
    before_update = session.updated_at

    session.add_user_message("Hello")

    assert len(session.messages) == 1
    assert isinstance(session.messages[-1], HumanMessage)
    assert session.messages[-1].content == "Hello"
    assert session.updated_at >= before_update


def test_session_add_assistant_message():
    """Test adding assistant messages."""
    session = FlowSession(session_id="sess-3a", user_id="user-3a")
    session.add_assistant_message("Hi there!")

    assert len(session.messages) == 1
    assert isinstance(session.messages[-1], AIMessage)
    assert session.messages[-1].content == "Hi there!"


def test_session_add_system_message():
    """Test adding system messages."""
    session = FlowSession(session_id="sess-3b", user_id="user-3b")
    session.add_system_message("You are a helpful assistant")

    assert len(session.messages) == 1
    assert isinstance(session.messages[-1], SystemMessage)
    assert session.messages[-1].content == "You are a helpful assistant"


def test_session_add_tool_message():
    """Test adding tool messages."""
    session = FlowSession(session_id="sess-3c", user_id="user-3c")
    session.add_tool_message("Search result", tool_call_id="call_123", name="search")

    assert len(session.messages) == 1
    assert isinstance(session.messages[-1], ToolMessage)
    assert session.messages[-1].content == "Search result"
    assert session.messages[-1].tool_call_id == "call_123"
    assert session.messages[-1].name == "search"


def test_session_add_message_with_base_message():
    """Test adding BaseMessage objects directly."""
    session = FlowSession(session_id="sess-3d", user_id="user-3d")
    msg = HumanMessage(content="Direct message", id="msg-1")
    session.add_message(msg)

    assert len(session.messages) == 1
    assert session.messages[-1] is msg
    assert session.messages[-1].id == "msg-1"


def test_session_get_history_limit():
    """Test getting limited message history."""
    session = FlowSession(session_id="sess-4", user_id="user-4")
    for idx in range(5):
        session.add_user_message(f"msg-{idx}")

    limited = session.get_history(limit=2)
    assert len(limited) == 2
    assert isinstance(limited[0], HumanMessage)
    assert limited[0].content == "msg-3"
    assert isinstance(limited[1], HumanMessage)
    assert limited[1].content == "msg-4"


def test_session_clear_history_resets_state():
    """Test that clearing history also clears custom state."""
    session = FlowSession(session_id="sess-5", user_id="user-5", state={"foo": "bar"})
    session.add_assistant_message("Here you go")

    session.clear_history()

    assert session.messages == []
    assert session.state == {}


def test_session_defaults():
    """Test default session values."""
    session = FlowSession(session_id="sess-6", user_id="user-6")

    assert session.workspace == Path("/tmp")
    assert session.interface == "unknown"
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)


def test_session_serialization_roundtrip():
    """Test that sessions can be serialized and deserialized correctly."""
    session = FlowSession(session_id="sess-7", user_id="user-7")
    session.add_user_message("Hello")
    session.add_assistant_message("Hi there!")
    session.add_system_message("System message")
    session.add_tool_message("Tool result", tool_call_id="call_123", name="search")

    # Serialize
    data = session.model_dump()
    assert isinstance(data["messages"], list)
    assert all(isinstance(msg, dict) for msg in data["messages"])

    # Deserialize
    restored = FlowSession.model_validate(data)
    assert len(restored.messages) == 4
    assert isinstance(restored.messages[0], HumanMessage)
    assert isinstance(restored.messages[1], AIMessage)
    assert isinstance(restored.messages[2], SystemMessage)
    assert isinstance(restored.messages[3], ToolMessage)
    assert restored.messages[0].content == "Hello"
    assert restored.messages[1].content == "Hi there!"
    assert restored.messages[3].tool_call_id == "call_123"


def test_session_validate_accepts_pydantic_kwargs():
    """Test that model_validate accepts Pydantic's keyword arguments."""
    data = {
        "session_id": "sess-8",
        "user_id": "user-8",
        "workspace": "/tmp",
        "messages": [],
    }

    # Should accept strict parameter (Pydantic validation option)
    session = FlowSession.model_validate(data, strict=False)
    assert session.session_id == "sess-8"

    # Should accept context parameter
    session_with_context = FlowSession.model_validate(data, context={"test": "value"})
    assert session_with_context.session_id == "sess-8"


def test_session_dump_respects_exclude():
    """Test that model_dump respects exclude parameter."""
    session = FlowSession(session_id="sess-9", user_id="user-9")
    session.add_user_message("Large message history")
    session.add_assistant_message("Response")

    # Exclude messages - should not include messages in output
    data = session.model_dump(exclude={"messages"})
    assert "messages" not in data
    assert "session_id" in data
    assert data["session_id"] == "sess-9"

    # Exclude workspace - should not include workspace
    data = session.model_dump(exclude={"workspace"})
    assert "workspace" not in data
    assert "messages" in data

    # Exclude both
    data = session.model_dump(exclude={"messages", "workspace"})
    assert "messages" not in data
    assert "workspace" not in data


def test_session_dump_respects_include():
    """Test that model_dump respects include parameter."""
    session = FlowSession(session_id="sess-10", user_id="user-10")
    session.add_user_message("Message")

    # Include only session_id - should only have session_id
    data = session.model_dump(include={"session_id"})
    assert "session_id" in data
    assert "messages" not in data
    assert "workspace" not in data
    assert "user_id" not in data

    # Include session_id and user_id only
    data = session.model_dump(include={"session_id", "user_id"})
    assert "session_id" in data
    assert "user_id" in data
    assert "messages" not in data
