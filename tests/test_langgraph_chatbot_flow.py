import pytest

from athos.config.models import ModelConfig
from athos.frameworks.langgraph.flows import chatbot
from athos.frameworks.langgraph.flows.chatbot import (
    LangGraphChatbotFlow,
    LangGraphChatbotFlowConfig,
    create_langgraph_chatbot_flow,
)
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput
from athos.models.session import FlowSession


class DummyAthosConfig:
    def __init__(self, model_cfg: ModelConfig) -> None:
        self.models = {"demo": model_cfg}


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

    flow = LangGraphChatbotFlow(DummyAthosConfig(ModelConfig(model_id="gpt-4o-mini")))
    await flow.initialize(cfg)

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

    flow = LangGraphChatbotFlow(DummyAthosConfig(ModelConfig(model_id="gpt-4o-mini")))
    await flow.initialize(cfg)

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

    assert len(chunks) == 3  # two chunks + final aggregate
    assert chunks[0].content == "Hel"
    assert chunks[0].metadata == {"streaming": True, "chunk": True}
    assert chunks[2].content == "Hello"
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

    flow = LangGraphChatbotFlow(DummyAthosConfig(ModelConfig(model_id="gpt-4o-mini")))
    await flow.initialize(cfg)

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


def test_chatbot_factory_returns_flow_instance():
    cfg = LangGraphChatbotFlowConfig(
        type="langgraph_chatbot",
        model="demo",
        system_prompt=None,
        initial_history=[],
    )

    flow = create_langgraph_chatbot_flow(
        cfg,
        DummyAthosConfig(ModelConfig(model_id="gpt-4o-mini")),
    )

    assert isinstance(flow, LangGraphChatbotFlow)
