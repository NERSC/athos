import pytest

from athos import build_config, build_flow
from athos.frameworks.langgraph.flows import agent as agent_module
from athos.frameworks.smolagents import flows as smol_flows  # noqa: F401


class DummyGraph:
    def __init__(self, response: str):
        self.response = response
        self.invocations = []

    async def ainvoke(self, state, config=None):
        self.invocations.append((state, config))
        messages = list(state["messages"])
        messages.append(agent_module.AIMessage(self.response))
        return {"messages": messages, "structured_response": self.response}


@pytest.mark.asyncio
async def test_langchain_web_agent_flow(monkeypatch):
    from pathlib import Path

    from athos.models.enums import ExecutionMode
    from athos.models.flow import FlowInput
    from athos.models.session import FlowSession

    monkeypatch.setenv("CBORG_API_URL", "https://api.example.com")
    monkeypatch.setenv("CBORG_API_KEY", "dummy-key")

    cfg = build_config("config/config.yaml")

    flow_cfg = cfg.flows["langchain_web_agent"]
    assert flow_cfg.type == "langchain_agent"
    assert flow_cfg.tools == ["langchain_tavily_search"]
    assert flow_cfg.max_iterations == 8

    class DummyModel:
        model_name = "test-model"

    dummy_model = DummyModel()
    dummy_tool = object()
    dummy_graph = DummyGraph("example agent summary")
    create_calls = []

    def fake_build_model(model_cfg):
        return dummy_model

    def fake_build_tool(tool_cfg):
        return dummy_tool

    def fake_create_agent(model, tools, *, system_prompt=None):
        create_calls.append(
            {
                "model": model,
                "tools": list(tools),
                "system_prompt": system_prompt,
            }
        )
        return dummy_graph

    monkeypatch.setattr(agent_module, "build_model", fake_build_model)
    monkeypatch.setattr(agent_module, "build_tool", fake_build_tool)
    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)

    flow = await build_flow("langchain_web_agent", cfg)

    assert flow.tools == [dummy_tool]
    assert flow.instructions is not None
    assert "web search tool" in flow.instructions.lower()

    session = FlowSession(
        session_id="test_session",
        user_id="test_user",
        workspace=Path("/tmp/test"),
    )

    input_data = FlowInput(
        message="Tell me about modern supercomputers",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    result = await flow.execute(input_data)
    assert result.content == "example agent summary"

    assert create_calls == [
        {
            "model": dummy_model,
            "tools": [dummy_tool],
            "system_prompt": flow.instructions,
        }
    ]

    assert dummy_graph.invocations[0][1] == {"recursion_limit": 8}
