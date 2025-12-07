from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
import pytest

from athos.models.message import Message, MessageRole


def test_to_langchain_converts_roles():
    user = Message(role=MessageRole.USER, content="hi")
    assistant = Message(role=MessageRole.ASSISTANT, content="hello")
    system = Message(role=MessageRole.SYSTEM, content="you are helpful")
    tool = Message(role=MessageRole.TOOL, content="42", name="calc", tool_call_id="call-1")

    lc_messages = Message.to_langchain_list([user, assistant, system, tool])

    assert isinstance(lc_messages[0], HumanMessage)
    assert isinstance(lc_messages[1], AIMessage)
    assert isinstance(lc_messages[2], SystemMessage)
    assert isinstance(lc_messages[3], ToolMessage)
    assert lc_messages[0].content == "hi"
    assert lc_messages[3].tool_call_id == "call-1"
    assert lc_messages[3].name == "calc"


def test_from_langchain_preserves_metadata_and_tool_calls():
    lc_ai = AIMessage(
        content="ok",
        metadata={"model": "gpt"},
        tool_calls=[{"id": "t1", "name": "search", "args": {"q": "hello"}}],
        id="msg-1",
        additional_kwargs={"foo": "bar"},
    )
    lc_tool = ToolMessage("result", name="search", tool_call_id="t1")

    messages = Message.from_langchain_list([lc_ai, lc_tool])

    assert messages[0].role is MessageRole.ASSISTANT
    assert messages[0].metadata == {"model": "gpt"}
    assert messages[0].tool_calls == lc_ai.tool_calls
    assert messages[0].id == "msg-1"
    assert messages[0].additional_kwargs["foo"] == "bar"

    assert messages[1].role is MessageRole.TOOL
    assert messages[1].tool_call_id == "t1"
    assert messages[1].name == "search"
    assert messages[1].content == "result"


def test_from_langchain_rejects_unknown_type():
    from langchain_core.messages import BaseMessage

    class UnknownMessage(BaseMessage):
        type: str = "unknown"

        def __init__(self, content: str) -> None:
            super().__init__(content=content)

    with pytest.raises(TypeError):
        Message.from_langchain(UnknownMessage(content="unknown"))
