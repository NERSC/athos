import asyncio

import pytest

from athos.core.flows import ChatbotFlow


class FakeResponse:
    """A fake response object that mimics the expected model response"""
    def __init__(self, content: str):
        self.content = content


class FakeModel:
    """A fake model that echoes the last user message"""
    def __call__(self, messages, stop_sequences=None):
        # Find the last user message in the list
        for msg in reversed(messages):
            if hasattr(msg, 'content') and hasattr(msg, 'role'):
                # Handle ChatMessage objects
                if msg.role == 'user':
                    return FakeResponse(f"echo: {msg.content}")
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                # Handle dict messages
                return FakeResponse(f"echo: {msg.get('content')}")
        return FakeResponse("")


def test_chatbot_flow_basic():
    fake_model = FakeModel()
    flow = ChatbotFlow(fake_model, system_prompt="SYSTEM_PROMPT")
    # First message
    response1 = asyncio.run(flow.execute("hello"))
    assert response1 == "echo: hello"
    # History should contain user and assistant messages
    assert len(flow.conversation_history) == 2
    assert flow.conversation_history[0] == {"role": "user", "content": "hello"}
    assert flow.conversation_history[1] == {"role": "assistant", "content": response1}

    # Second message
    response2 = asyncio.run(flow.process_message("world"))
    assert response2 == "echo: world"
    # History now contains four entries
    assert len(flow.conversation_history) == 4
    # All roles in history are user or assistant
    roles = {entry.get('role') for entry in flow.conversation_history}
    assert roles <= {"user", "assistant"}


def test_chatbot_flow_without_system_prompt():
    fake_model = FakeModel()
    flow = ChatbotFlow(fake_model)
    response = asyncio.run(flow.execute("test"))
    assert response == "echo: test"
    # System prompt should not appear in history
    for entry in flow.conversation_history:
        assert entry.get('role') in ("user", "assistant")