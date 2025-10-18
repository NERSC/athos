import pytest

from athos.config.models import ModelConfig
from athos.frameworks.langgraph.flows import chatbot
from athos.frameworks.langgraph.flows.chatbot import (
    LangGraphChatbotFlow,
    LangGraphChatbotFlowConfig,
    create_langgraph_chatbot_flow,
)


class DummyModel:
    def __init__(self):
        self.invocations = []

    async def ainvoke(self, messages):
        self.invocations.append(messages)
        return chatbot.AIMessage("Hello back!")


@pytest.mark.asyncio
async def test_chatbot_flow_roundtrip():
    model = DummyModel()
    flow = LangGraphChatbotFlow(
        model=model,
        system_prompt="You are a helpful assistant.",
        initial_history=[chatbot.HumanMessage("Hi"), chatbot.AIMessage("Hello")],
    )

    reply = await flow.execute("How are you?")

    assert reply == "Hello back!"
    assert len(model.invocations) == 1
    messages = model.invocations[0]
    assert messages[0].content == "You are a helpful assistant."
    assert messages[-1].content == "How are you?"
    assert flow._history[-1].content == "Hello back!"


def test_chatbot_factory_builds_flow(monkeypatch):
    dummy_model = DummyModel()

    def fake_build_model(model_cfg):
        assert model_cfg.model_id == "gpt-4o-mini"
        return dummy_model

    monkeypatch.setattr(chatbot, "build_model", fake_build_model)

    cfg = LangGraphChatbotFlowConfig(
        type="langgraph_chatbot",
        model="demo",
        system_prompt="System",
        initial_history=["Hi", "Hey there"],
    )

    class DummyAthosConfig:
        models = {"demo": ModelConfig(model_id="gpt-4o-mini")}

    flow = create_langgraph_chatbot_flow(cfg, DummyAthosConfig())

    assert flow.model is dummy_model
    assert flow._system_message.content == "System"
