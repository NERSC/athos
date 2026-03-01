"""Tests for LangChainAgentFlow checkpoint integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from athos.config.models import AthosConfig, ModelConfig
from athos.frameworks.langgraph.flows.agent import LangChainAgentFlow, LangChainAgentFlowConfig
from athos.models.flow import FlowInput, FlowSession
from athos.models.enums import ExecutionMode
from athos.models.message import Message

# Test constants
SESSION_ID_BASIC = "test-session-basic"
SESSION_ID_SYNC = "test-session-sync"
SESSION_ID_STREAM = "test-session-stream"
SESSION_ID_PERSISTENCE = "test-session-persistence"
USER_ID = "test-user-1"


@pytest.fixture
def mock_model():
    """Create a mock LangChain model."""
    model = MagicMock()
    model.model_name = "gpt-4"

    # Add bind method for tool binding
    model.bind = MagicMock(return_value=model)

    # Add default ainvoke behavior
    from langchain_core.messages import AIMessage
    async def default_ainvoke(messages, config=None):
        return AIMessage(content="Test response")
    model.ainvoke = AsyncMock(side_effect=default_ainvoke)

    return model


@pytest.fixture
def flow_config():
    """Create a basic flow configuration."""
    return LangChainAgentFlowConfig(
        type="langchain_agent",
        model="gpt_4",
        tools=[],
        mcp_servers=[],
        system_prompt="You are a helpful assistant.",
        max_iterations=10,
    )


@pytest.fixture
def athos_config(tmp_path):
    """Create a minimal ATHOS configuration."""
    return AthosConfig(
        models={
            "gpt_4": ModelConfig(
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
async def flow(mock_model, flow_config, athos_config):
    """Create a flow instance with automatic cleanup."""
    with patch("athos.frameworks.langgraph.flows.agent.build_model", return_value=mock_model):
        flow_instance = await LangChainAgentFlow.create(flow_config, athos_config)
        yield flow_instance
        await flow_instance.cleanup()


@pytest.mark.asyncio
async def test_checkpointer_initialized(flow):
    """Test that InMemorySaver checkpointer is created during graph build.

    The checkpointer is lazily initialized when the graph is first built.
    This enables checkpoint-based conversation memory persistence.
    """
    # Checkpointer should be None before graph is built
    assert flow._checkpointer is None

    # Build the graph
    await flow._ensure_graph_built()

    # Checkpointer should now exist
    assert flow._checkpointer is not None
    from langgraph.checkpoint.memory import InMemorySaver
    assert isinstance(flow._checkpointer, InMemorySaver)


@pytest.mark.asyncio
async def test_build_langgraph_config(flow):
    """Test that _build_langgraph_config creates proper RunnableConfig.

    The config must include thread_id in the configurable section for
    checkpoint-based state management to work correctly.
    """
    config = flow._build_langgraph_config(SESSION_ID_BASIC)

    # Check structure
    assert "configurable" in config
    assert config["configurable"]["thread_id"] == SESSION_ID_BASIC
    assert config["recursion_limit"] == flow.max_iterations


@pytest.mark.asyncio
async def test_build_messages_only_new_message(flow):
    """Test that _build_messages only returns the new user message, not history.

    When checkpointing is enabled, conversation history is automatically loaded
    from the checkpoint store using thread_id. Therefore, _build_messages should
    only return the current user message, letting the checkpoint provide all
    previous messages in the conversation.

    This design prevents duplicate message history and ensures the checkpoint
    is the single source of truth for conversation state.
    """
    # Create session with existing history
    session = FlowSession(
        session_id=SESSION_ID_BASIC,
        user_id=USER_ID,
        messages=[
            Message(role="user", content="First message"),
            Message(role="assistant", content="First response"),
            Message(role="user", content="Second message"),
            Message(role="assistant", content="Second response"),
        ],
    )

    flow_input = FlowInput(
        message=Message(role="user", content="Third message"),
        session=session,
        mode=ExecutionMode.SYNC,
    )

    messages = flow._build_messages(flow_input)

    # Should only contain the new message
    assert len(messages) == 1
    assert messages[0].content == "Third message"


@pytest.mark.asyncio
async def test_execute_uses_thread_id(flow):
    """Test that execute() passes thread_id in config to graph.ainvoke()."""
    from langchain_core.messages import AIMessage

    # Mock the graph with proper async behavior
    mock_ainvoke = AsyncMock(return_value={
        "messages": [AIMessage(content="Test response")]
    })

    # Mock the ensure methods to skip initialization
    flow._ensure_mcp_tools_loaded = AsyncMock()
    flow._ensure_graph_built = AsyncMock()

    flow._graph = MagicMock()
    flow._graph.ainvoke = mock_ainvoke

    session = FlowSession(session_id=SESSION_ID_SYNC, user_id=USER_ID)
    flow_input = FlowInput(message="Hello", session=session, mode=ExecutionMode.SYNC)

    await flow.execute(flow_input)

    # Verify ainvoke was called with correct config
    mock_ainvoke.assert_called_once()
    call_args = mock_ainvoke.call_args
    config_arg = call_args[1]["config"]

    assert config_arg["configurable"]["thread_id"] == SESSION_ID_SYNC
    assert config_arg["recursion_limit"] == flow.max_iterations


@pytest.mark.asyncio
async def test_execute_metadata_includes_checkpoint_info(flow):
    """Test that execute() output metadata includes checkpoint information."""
    from langchain_core.messages import AIMessage

    # Mock the graph with proper async behavior
    mock_ainvoke = AsyncMock(return_value={
        "messages": [AIMessage(content="Test response")]
    })

    # Mock the ensure methods to skip initialization
    flow._ensure_mcp_tools_loaded = AsyncMock()
    flow._ensure_graph_built = AsyncMock()

    flow._graph = MagicMock()
    flow._graph.ainvoke = mock_ainvoke

    session = FlowSession(session_id=SESSION_ID_BASIC, user_id=USER_ID)
    flow_input = FlowInput(message="Hello", session=session, mode=ExecutionMode.SYNC)

    output = await flow.execute(flow_input)

    # Verify metadata
    assert output.metadata["checkpoint_enabled"] is True
    assert output.metadata["thread_id"] == SESSION_ID_BASIC


@pytest.mark.asyncio
async def test_execute_includes_langgraph_debug_metadata_when_requested(flow):
    """Test that debug_include_steps returns framework-agnostic step/state debug payload."""
    from langchain_core.messages import AIMessage

    mock_ainvoke = AsyncMock(return_value={
        "messages": [AIMessage(content="Test response")],
        "structured_response": None,
    })

    flow._ensure_mcp_tools_loaded = AsyncMock()
    flow._ensure_graph_built = AsyncMock()
    flow._graph = MagicMock()
    flow._graph.ainvoke = mock_ainvoke

    session = FlowSession(session_id=SESSION_ID_BASIC, user_id=USER_ID)
    flow_input = FlowInput(
        message="Hello",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={"debug_include_steps": True},
    )

    output = await flow.execute(flow_input)

    assert "langgraph_steps" in output.metadata
    assert "langgraph_state" in output.metadata
    assert isinstance(output.metadata["langgraph_steps"], list)
    assert output.metadata["langgraph_steps"][0]["message_type"] == "AIMessage"
    assert output.metadata["langgraph_steps"][0]["content"] == "Test response"
    assert output.metadata["langgraph_state"]["message_count"] == 1


@pytest.mark.asyncio
async def test_execute_includes_raw_langgraph_debug_payload_at_high_verbosity(flow):
    """Test runtime verbosity override enables raw payload emission for debug dumps."""
    from langchain_core.messages import AIMessage

    mock_ainvoke = AsyncMock(return_value={
        "messages": [AIMessage(content="Test response")],
        "structured_response": None,
    })

    flow._ensure_mcp_tools_loaded = AsyncMock()
    flow._ensure_graph_built = AsyncMock()
    flow._graph = MagicMock()
    flow._graph.ainvoke = mock_ainvoke

    session = FlowSession(session_id=SESSION_ID_BASIC, user_id=USER_ID)
    flow_input = FlowInput(
        message="Hello",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={"debug_include_steps": True, "verbosity_level": 3},
    )

    output = await flow.execute(flow_input)

    assert "raw" in output.metadata["langgraph_steps"][0]
    assert "raw" in output.metadata["langgraph_state"]


@pytest.mark.asyncio
async def test_stream_uses_thread_id(flow):
    """Test that stream() passes thread_id in config to graph.astream().

    The streaming interface must pass the same checkpoint config as execute()
    to ensure conversation state is maintained across both sync and streaming calls.
    """
    # Capture the config passed to astream
    captured_config = {}

    async def mock_astream(input, config=None, stream_mode=None):
        """Async generator that captures config and yields test chunks."""
        captured_config['config'] = config
        # Yield a final message chunk
        from langchain_core.messages import AIMessageChunk
        yield ("messages", (AIMessageChunk(content="Test"), {"langgraph_node": "model"}))

    # Mock the ensure methods to skip initialization
    flow._ensure_mcp_tools_loaded = AsyncMock()
    flow._ensure_graph_built = AsyncMock()

    # Mock the graph
    mock_graph = MagicMock()
    mock_graph.astream = mock_astream
    flow._graph = mock_graph
    flow._checkpointer = MagicMock()

    session = FlowSession(session_id=SESSION_ID_STREAM, user_id=USER_ID)
    flow_input = FlowInput(message="Hello stream", session=session, mode=ExecutionMode.STREAMING)

    # Consume the stream
    chunks = []
    async for chunk in flow.stream(flow_input):
        chunks.append(chunk)

    # Verify we got output
    assert len(chunks) > 0

    # Verify the config was passed correctly
    assert captured_config['config'] is not None
    assert captured_config['config']['configurable']['thread_id'] == SESSION_ID_STREAM
    assert captured_config['config']['recursion_limit'] == flow.max_iterations


@pytest.mark.asyncio
async def test_checkpoint_persists_conversation_state(flow):
    """Test that checkpointer actually persists and restores conversation state.

    This test verifies the core checkpoint functionality by checking that
    the checkpoint store accumulates state across multiple execute() calls.
    """
    from langgraph.checkpoint.memory import InMemorySaver

    # Build the graph to initialize the checkpointer
    await flow._ensure_graph_built()

    checkpointer: InMemorySaver = flow._checkpointer
    assert checkpointer is not None

    session = FlowSession(session_id=SESSION_ID_PERSISTENCE, user_id=USER_ID)
    config = {"configurable": {"thread_id": SESSION_ID_PERSISTENCE}}

    # First execution
    input1 = FlowInput(message="First message", session=session, mode=ExecutionMode.SYNC)
    await flow.execute(input1)

    # Check checkpoint after first turn
    checkpoint_1 = checkpointer.get_tuple(config)
    assert checkpoint_1 is not None
    messages_1 = checkpoint_1.checkpoint['channel_values']['messages']
    # Should have system message + user message + AI response
    assert len(messages_1) >= 2  # At least user + AI

    # Second execution with same session
    input2 = FlowInput(message="Second message", session=session, mode=ExecutionMode.SYNC)
    await flow.execute(input2)

    # Check checkpoint after second turn
    checkpoint_2 = checkpointer.get_tuple(config)
    assert checkpoint_2 is not None
    messages_2 = checkpoint_2.checkpoint['channel_values']['messages']
    # Should have grown: system + turn1_user + turn1_AI + turn2_user + turn2_AI
    assert len(messages_2) > len(messages_1)

    # Third execution with same session
    input3 = FlowInput(message="Third message", session=session, mode=ExecutionMode.SYNC)
    await flow.execute(input3)

    # Check checkpoint after third turn
    checkpoint_3 = checkpointer.get_tuple(config)
    assert checkpoint_3 is not None
    messages_3 = checkpoint_3.checkpoint['channel_values']['messages']
    # Should continue growing
    assert len(messages_3) > len(messages_2)

    # Verify message content
    message_contents = [msg.content for msg in messages_3]
    assert "First message" in message_contents
    assert "Second message" in message_contents
    assert "Third message" in message_contents


@pytest.mark.asyncio
async def test_different_thread_ids_have_separate_checkpoints(flow):
    """Test that different thread_ids maintain isolated conversation states.

    This verifies that the checkpoint system properly isolates conversations
    by thread_id, preventing state leakage between different sessions.
    """
    from langgraph.checkpoint.memory import InMemorySaver

    await flow._ensure_graph_built()
    checkpointer: InMemorySaver = flow._checkpointer

    # Execute with first session
    session1 = FlowSession(session_id="thread-1", user_id=USER_ID)
    await flow.execute(FlowInput(message="Message 1 to thread 1", session=session1, mode=ExecutionMode.SYNC))
    await flow.execute(FlowInput(message="Message 2 to thread 1", session=session1, mode=ExecutionMode.SYNC))

    # Execute with second session
    session2 = FlowSession(session_id="thread-2", user_id=USER_ID)
    await flow.execute(FlowInput(message="Message 1 to thread 2", session=session2, mode=ExecutionMode.SYNC))

    # Check checkpoint state for each thread
    config1 = {"configurable": {"thread_id": "thread-1"}}
    config2 = {"configurable": {"thread_id": "thread-2"}}

    checkpoint_1 = checkpointer.get_tuple(config1)
    checkpoint_2 = checkpointer.get_tuple(config2)

    assert checkpoint_1 is not None
    assert checkpoint_2 is not None

    messages_1 = checkpoint_1.checkpoint['channel_values']['messages']
    messages_2 = checkpoint_2.checkpoint['channel_values']['messages']

    # Thread 1 has 2 turns, thread 2 has 1 turn
    assert len(messages_1) > len(messages_2)

    # Verify thread 1 has both its messages
    contents_1 = [msg.content for msg in messages_1]
    assert "Message 1 to thread 1" in contents_1
    assert "Message 2 to thread 1" in contents_1
    assert "Message 1 to thread 2" not in contents_1  # No leakage

    # Verify thread 2 has only its message
    contents_2 = [msg.content for msg in messages_2]
    assert "Message 1 to thread 2" in contents_2
    assert "Message 1 to thread 1" not in contents_2  # No leakage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
