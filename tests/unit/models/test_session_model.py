from datetime import datetime
from pathlib import Path

from athos.models import FlowSession, Message, MessageRole


def test_session_add_user_message_updates_history_and_timestamp():
    session = FlowSession(session_id="sess-3", user_id="user-3")
    before_update = session.updated_at

    session.add_user_message("Hello")

    assert session.messages[-1].content == "Hello"
    assert session.messages[-1].role is MessageRole.USER
    assert session.updated_at >= before_update


def test_session_add_message_accepts_message_object():
    session = FlowSession(session_id="sess-3a", user_id="user-3a")
    msg = Message(role=MessageRole.ASSISTANT, content="Hi there")

    session.add_message(msg)

    assert session.messages[-1] is msg
    assert session.messages[-1].role is MessageRole.ASSISTANT


def test_session_get_history_limit():
    session = FlowSession(session_id="sess-4", user_id="user-4")
    for idx in range(5):
        session.add_user_message(f"msg-{idx}")

    limited = session.get_history(limit=2)
    assert len(limited) == 2
    assert limited[0].content == "msg-3"
    assert limited[1].content == "msg-4"


def test_session_clear_history_resets_state():
    session = FlowSession(session_id="sess-5", user_id="user-5", state={"foo": "bar"})
    session.add_assistant_message("Here you go")

    session.clear_history()

    assert session.messages == []
    assert session.state == {}


def test_session_defaults():
    session = FlowSession(session_id="sess-6", user_id="user-6")

    assert session.workspace == Path("/tmp")
    assert session.interface == "unknown"
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)
