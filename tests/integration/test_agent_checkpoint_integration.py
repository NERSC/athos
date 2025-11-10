"""Integration tests for LangChainAgentFlow checkpoint functionality.

These tests verify end-to-end checkpoint behavior including graph construction,
state persistence, and conversation memory across multiple turns. Unlike unit
tests that mock internal components, these tests verify the actual checkpoint
integration with minimal mocking.
"""

import pytest
from unittest.mock import patch, AsyncMock

from athos.config.models import AthosConfig, ModelConfig
from athos.frameworks.langgraph.flows.agent import LangChainAgentFlow, LangChainAgentFlowConfig
from athos.models.flow import FlowInput, FlowSession
from athos.models.enums import ExecutionMode

# Test constants
SESSION_ID_ALICE = "integration-session-alice"
SESSION_ID_BOB = "integration-session-bob"
SESSION_ID_FRESH = "integration-session-fresh"
USER_ID = "integration-user-1"


@pytest.fixture
def flow_config():
    """Create a basic flow configuration for testing."""
    return LangChainAgentFlowConfig(
        type="langchain_agent",
        model="test_model",
        tools=[],
        mcp_servers=[],
        system_prompt="You are a helpful assistant that remembers context from the conversation.",
        max_iterations=10,
    )


@pytest.fixture
def athos_config(tmp_path):
    """Create ATHOS configuration."""
    return AthosConfig(
        models={
            "test_model": ModelConfig(
                model_id="gpt-4",
                api_key="test-key",
            )
        },
        flows={},
        mcp_servers={},
        tools={},
        workspace_dir=str(tmp_path),
    )


@pytest.fixture
def mock_conversational_model():
    """Create a mock model that simulates contextual conversation.

    This mock tracks the conversation context passed to it and generates
    responses that demonstrate understanding of conversation history.
    """
    from langchain_core.messages import AIMessage

    # Track all invocations
    invocation_log = []

    async def contextual_ainvoke(messages, config=None):
        """Simulate a model that uses conversation history."""
        # Log this invocation for test verification
        invocation_log.append({
            'message_count': len(messages),
            'last_user_message': messages[-1].content if messages else None,
            'thread_id': config.get('configurable', {}).get('thread_id') if config else None,
        })

        # Get the last user message
        last_message = messages[-1].content.lower() if messages else ""

        # Simulate contextual responses based on history
        if "how many messages" in last_message or "how many times" in last_message:
            # Count user messages in history
            user_msg_count = sum(1 for msg in messages if hasattr(msg, 'type') and msg.type == 'human')
            return AIMessage(content=f"You've sent {user_msg_count} messages so far.")

        elif "what did i say" in last_message or "first message" in last_message:
            # Find the first user message
            for msg in messages:
                if hasattr(msg, 'type') and msg.type == 'human':
                    return AIMessage(content=f"Your first message was: {msg.content}")
            return AIMessage(content="I don't see any previous messages.")

        else:
            # Default response that shows message count
            msg_count = len(messages)
            return AIMessage(content=f"I received your message. (Context: {msg_count} messages in history)")

    # Create mock with tracking
    mock = AsyncMock()
    mock.ainvoke = contextual_ainvoke
    mock.model_name = "integration-test-model"
    mock.bind = lambda **kwargs: mock
    mock._invocation_log = invocation_log  # Expose for test assertions

    return mock


@pytest.fixture
async def flow(mock_conversational_model, flow_config, athos_config):
    """Create a flow instance with automatic cleanup."""
    with patch("athos.frameworks.langgraph.flows.agent.build_model", return_value=mock_conversational_model):
        flow_instance = await LangChainAgentFlow.create(flow_config, athos_config)
        yield flow_instance
        await flow_instance.cleanup()


@pytest.mark.asyncio
async def test_checkpoint_maintains_conversation_context_across_turns(flow, mock_conversational_model):
    """Test that checkpoint preserves conversation context across multiple execute() calls.

    This integration test verifies that:
    1. Each subsequent call stores messages in the checkpoint
    2. The checkpoint accumulates conversation history
    3. All interactions use the same thread_id for checkpoint lookup
    """
    from langgraph.checkpoint.memory import InMemorySaver

    session = FlowSession(session_id=SESSION_ID_ALICE, user_id=USER_ID)

    # Turn 1
    output1 = await flow.execute(FlowInput(
        message="Hello, this is my first message",
        session=session,
        mode=ExecutionMode.SYNC
    ))

    # Check checkpoint after turn 1
    await flow._ensure_graph_built()
    checkpointer: InMemorySaver = flow._checkpointer
    config = {"configurable": {"thread_id": SESSION_ID_ALICE}}
    checkpoint_1 = checkpointer.get_tuple(config)
    assert checkpoint_1 is not None
    messages_1 = checkpoint_1.checkpoint['channel_values']['messages']
    initial_count = len(messages_1)

    # Turn 2
    output2 = await flow.execute(FlowInput(
        message="This is my second message",
        session=session,
        mode=ExecutionMode.SYNC
    ))

    # Check checkpoint after turn 2 - should have more messages
    checkpoint_2 = checkpointer.get_tuple(config)
    messages_2 = checkpoint_2.checkpoint['channel_values']['messages']
    assert len(messages_2) > initial_count

    # Turn 3
    output3 = await flow.execute(FlowInput(
        message="How many messages have I sent?",
        session=session,
        mode=ExecutionMode.SYNC
    ))

    # Check final checkpoint - should continue growing
    checkpoint_3 = checkpointer.get_tuple(config)
    messages_3 = checkpoint_3.checkpoint['channel_values']['messages']
    assert len(messages_3) > len(messages_2)

    # Verify all user messages are in the checkpoint
    message_contents = [msg.content for msg in messages_3]
    assert "Hello, this is my first message" in message_contents
    assert "This is my second message" in message_contents
    assert "How many messages have I sent?" in message_contents


@pytest.mark.asyncio
async def test_different_sessions_maintain_separate_checkpoint_states(flow, mock_conversational_model):
    """Test that different session_ids maintain completely isolated conversation states.

    This verifies checkpoint isolation: sessions must not share state or leak
    information between different thread_ids.
    """
    from langgraph.checkpoint.memory import InMemorySaver

    await flow._ensure_graph_built()
    checkpointer: InMemorySaver = flow._checkpointer

    # Alice's conversation
    session_alice = FlowSession(session_id=SESSION_ID_ALICE, user_id=USER_ID)
    await flow.execute(FlowInput(message="Alice message 1", session=session_alice, mode=ExecutionMode.SYNC))
    await flow.execute(FlowInput(message="Alice message 2", session=session_alice, mode=ExecutionMode.SYNC))
    await flow.execute(FlowInput(message="Alice message 3", session=session_alice, mode=ExecutionMode.SYNC))

    # Bob's conversation (separate session)
    session_bob = FlowSession(session_id=SESSION_ID_BOB, user_id=USER_ID)
    await flow.execute(FlowInput(message="Bob message 1", session=session_bob, mode=ExecutionMode.SYNC))

    # Check checkpoint states
    config_alice = {"configurable": {"thread_id": SESSION_ID_ALICE}}
    config_bob = {"configurable": {"thread_id": SESSION_ID_BOB}}

    checkpoint_alice = checkpointer.get_tuple(config_alice)
    checkpoint_bob = checkpointer.get_tuple(config_bob)

    assert checkpoint_alice is not None
    assert checkpoint_bob is not None

    messages_alice = checkpoint_alice.checkpoint['channel_values']['messages']
    messages_bob = checkpoint_bob.checkpoint['channel_values']['messages']

    # Alice should have more messages (3 turns vs 1 turn)
    assert len(messages_alice) > len(messages_bob)

    # Verify Alice's messages don't contain Bob's content
    alice_contents = [msg.content for msg in messages_alice]
    assert "Alice message 1" in alice_contents
    assert "Alice message 2" in alice_contents
    assert "Alice message 3" in alice_contents
    assert "Bob message 1" not in alice_contents

    # Verify Bob's messages don't contain Alice's content
    bob_contents = [msg.content for msg in messages_bob]
    assert "Bob message 1" in bob_contents
    assert "Alice message 1" not in bob_contents
    assert "Alice message 2" not in bob_contents
    assert "Alice message 3" not in bob_contents


@pytest.mark.asyncio
async def test_new_session_starts_with_clean_checkpoint_state(flow, mock_conversational_model):
    """Test that a new session has no checkpoint history.

    This verifies that each new thread_id starts fresh without any
    residual state from other sessions.
    """
    from langgraph.checkpoint.memory import InMemorySaver

    await flow._ensure_graph_built()
    checkpointer: InMemorySaver = flow._checkpointer

    # Create a completely new session
    fresh_session = FlowSession(session_id=SESSION_ID_FRESH, user_id=USER_ID)

    # First message in this session
    output = await flow.execute(FlowInput(
        message="This is my first message",
        session=fresh_session,
        mode=ExecutionMode.SYNC
    ))

    # Check checkpoint - should only have messages from this single turn
    config = {"configurable": {"thread_id": SESSION_ID_FRESH}}
    checkpoint = checkpointer.get_tuple(config)
    assert checkpoint is not None

    messages = checkpoint.checkpoint['channel_values']['messages']

    # Should have system message + user message + AI response
    # No history from other sessions
    message_contents = [msg.content for msg in messages]
    assert "This is my first message" in message_contents

    # Should not have messages from other sessions
    assert "Alice message" not in str(message_contents)
    assert "Bob message" not in str(message_contents)


@pytest.mark.asyncio
async def test_checkpoint_persists_across_graph_rebuilds(mock_conversational_model, flow_config, athos_config):
    """Test checkpoint behavior when flow is recreated.

    Note: With InMemorySaver, checkpoint state is lost when flow is recreated.
    This test documents current behavior. With a persistent checkpointer
    (SQLite, Redis), state would survive flow recreation.
    """
    from langgraph.checkpoint.memory import InMemorySaver

    session = FlowSession(session_id="rebuild-test", user_id=USER_ID)

    # Create first flow instance
    with patch("athos.frameworks.langgraph.flows.agent.build_model", return_value=mock_conversational_model):
        flow1 = await LangChainAgentFlow.create(flow_config, athos_config)

        # Have a conversation
        await flow1.execute(FlowInput(message="Message 1", session=session, mode=ExecutionMode.SYNC))
        await flow1.execute(FlowInput(message="Message 2", session=session, mode=ExecutionMode.SYNC))

        # Check checkpoint in first flow
        await flow1._ensure_graph_built()
        checkpointer1: InMemorySaver = flow1._checkpointer
        config = {"configurable": {"thread_id": "rebuild-test"}}
        checkpoint1 = checkpointer1.get_tuple(config)
        assert checkpoint1 is not None
        messages1 = checkpoint1.checkpoint['channel_values']['messages']
        assert len(messages1) >= 2  # At least 2 turns

        # Clean up first flow
        await flow1.cleanup()

        # Create second flow instance (same session, new flow)
        flow2 = await LangChainAgentFlow.create(flow_config, athos_config)
        await flow2._ensure_graph_built()
        checkpointer2: InMemorySaver = flow2._checkpointer

        # With InMemorySaver, the checkpoint is a new instance
        # Check if checkpoint from first flow exists (it won't)
        checkpoint2 = checkpointer2.get_tuple(config)

        # This is None because InMemorySaver doesn't persist across instances
        assert checkpoint2 is None

        # If we execute in the second flow, it starts fresh
        await flow2.execute(FlowInput(message="Message 3", session=session, mode=ExecutionMode.SYNC))

        checkpoint3 = checkpointer2.get_tuple(config)
        assert checkpoint3 is not None
        messages3 = checkpoint3.checkpoint['channel_values']['messages']

        # Should not have messages from first flow (InMemorySaver doesn't persist)
        contents = [msg.content for msg in messages3]
        assert "Message 3" in contents
        # Message 1 and 2 were in the first flow's checkpoint, which is now gone
        assert "Message 1" not in contents
        assert "Message 2" not in contents

        await flow2.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
