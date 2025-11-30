import pytest

from athos.config.models import AthosConfig, ModelConfig
from athos.frameworks.langgraph.flows import chatbot
from athos.frameworks.langgraph.flows.chatbot import (
    LangGraphChatbotFlow,
    LangGraphChatbotFlowConfig,
)
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput
from athos.models.metrics import ExecutionMetrics
from athos.models.session import FlowSession


def create_dummy_config(model_cfg: ModelConfig) -> AthosConfig:
    """Create a minimal AthosConfig for testing."""
    return AthosConfig(
        models={"demo": model_cfg},
        flows={},
        mcp_servers={},
        tools={},
        workspace_dir="/tmp/test_workspace",
    )


class DummyModel:
    def __init__(self) -> None:
        self.invocations = []
        self.model_name = "dummy-model"

    async def ainvoke(self, messages):
        self.invocations.append(messages)
        return chatbot.AIMessage("Hello back!")


class StreamingDummyModel(DummyModel):
    async def astream(self, messages):
        self.invocations.append(messages)
        for chunk in ("Hel", "lo"):
            yield chatbot.AIMessage(chunk)


class FailingModel(DummyModel):
    async def ainvoke(self, messages):
        raise RuntimeError("Model API error: connection timeout")


class MetricsDummyModel(DummyModel):
    def __init__(self) -> None:
        super().__init__()

        class Response:
            def __init__(self):
                self.content = "Hello metrics!"
                self.usage_metadata = type(
                    "Usage",
                    (),
                    {"input_tokens": 10, "output_tokens": 5},
                )()

        self.response = Response()

    async def ainvoke(self, messages):
        self.invocations.append(messages)
        return self.response


@pytest.mark.asyncio
async def test_chatbot_flow_execute_returns_structured_output(monkeypatch):
    dummy_model = DummyModel()
    monkeypatch.setattr(chatbot, "build_model", lambda cfg: dummy_model)

    cfg = LangGraphChatbotFlowConfig(
        type="langgraph_chatbot",
        model="demo",
        system_prompt="System prompt",
        initial_history=["Hi", "Hello there"],
    )

    athos_config = create_dummy_config(ModelConfig(model_id="gpt-4o-mini"))
    flow = await LangGraphChatbotFlow.create(cfg, athos_config)

    session = FlowSession(session_id="s", user_id="u")
    session.add_message("user", "Previous question")
    session.add_message("assistant", "Previous answer")

    flow_input = FlowInput(
        message="How are you?",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    output = await flow.execute(flow_input)

    assert output.content == "Hello back!"
    assert output.metadata["model"] == "dummy-model"
    assert len(dummy_model.invocations) == 1
    messages = dummy_model.invocations[0]
    assert messages[0].content == "System prompt"
    assert messages[1].content == "Hi"
    assert messages[-1].content == "How are you?"


@pytest.mark.asyncio
async def test_chatbot_flow_streams_chunks_then_final_response(monkeypatch):
    streaming_model = StreamingDummyModel()
    monkeypatch.setattr(chatbot, "build_model", lambda cfg: streaming_model)

    cfg = LangGraphChatbotFlowConfig(
        type="langgraph_chatbot",
        model="demo",
        system_prompt=None,
        initial_history=[],
    )

    athos_config = create_dummy_config(ModelConfig(model_id="gpt-4o-mini"))
    flow = await LangGraphChatbotFlow.create(cfg, athos_config)

    session = FlowSession(session_id="s", user_id="u")
    flow_input = FlowInput(
        message="Hello",
        session=session,
        mode=ExecutionMode.STREAMING,
        metadata={},
    )

    chunks = []
    async for item in flow.stream(flow_input):
        chunks.append(item)

    assert len(chunks) == 3  # two chunks + final message
    assert chunks[0].content == "Hel"
    assert chunks[0].metadata == {"streaming": True, "chunk": True}
    assert chunks[2].content == ""
    assert chunks[2].metadata["final"] is True


@pytest.mark.asyncio
async def test_chatbot_flow_handles_exceptions_gracefully(monkeypatch):
    failing_model = FailingModel()
    monkeypatch.setattr(chatbot, "build_model", lambda cfg: failing_model)

    cfg = LangGraphChatbotFlowConfig(
        type="langgraph_chatbot",
        model="demo",
        system_prompt="System",
        initial_history=[],
    )

    athos_config = create_dummy_config(ModelConfig(model_id="gpt-4o-mini"))
    flow = await LangGraphChatbotFlow.create(cfg, athos_config)

    session = FlowSession(session_id="s", user_id="u")
    flow_input = FlowInput(
        message="Tell me a joke",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    output = await flow.execute(flow_input)

    assert output.content.startswith("Error:")
    assert output.metadata["error"] is True
    assert output.metadata["exception_type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_chatbot_create_returns_flow_instance(monkeypatch):
    """Test that create() classmethod returns a properly initialized flow."""
    dummy_model = DummyModel()
    monkeypatch.setattr(chatbot, "build_model", lambda cfg: dummy_model)

    cfg = LangGraphChatbotFlowConfig(
        type="langgraph_chatbot",
        model="demo",
        system_prompt=None,
        initial_history=[],
    )

    athos_config = create_dummy_config(ModelConfig(model_id="gpt-4o-mini"))
    flow = await LangGraphChatbotFlow.create(cfg, athos_config)

    assert isinstance(flow, LangGraphChatbotFlow)
    assert flow.model == dummy_model
    assert flow.system_prompt is None
    assert flow._initial_history == []


@pytest.mark.asyncio
async def test_chatbot_flow_records_execution_metrics(monkeypatch):
    metrics_model = MetricsDummyModel()
    monkeypatch.setattr(chatbot, "build_model", lambda cfg: metrics_model)

    cfg = LangGraphChatbotFlowConfig(
        type="langgraph_chatbot",
        model="demo",
        system_prompt=None,
        initial_history=[],
    )

    athos_config = create_dummy_config(ModelConfig(model_id="gpt-4o-mini"))
    flow = await LangGraphChatbotFlow.create(cfg, athos_config)

    flow_input = FlowInput(
        message="Hi",
        session=FlowSession(session_id="s", user_id="u"),
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    result = await flow.execute(flow_input)

    assert result.metadata["token_usage"] == {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }
    assert result.metadata["tool_calls"] == []
    assert result.metadata["step_count"] == 1

    metrics = ExecutionMetrics.from_metadata(result.metadata)
    assert metrics is not None
    assert metrics.step_count == 1
    assert metrics.token_usage.total_tokens == 15
    assert metrics.tool_calls == []
