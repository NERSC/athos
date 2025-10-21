import pytest

from athos import build_config, build_flow
from athos.frameworks.langgraph.flows import react_agent


class DummyGraph:
    def __init__(self, response: str):
        self.response = response
        self.invocations = []

    async def ainvoke(self, state, config=None):
        self.invocations.append((state, config))
        messages = list(state["messages"])
        messages.append(react_agent.AIMessage(self.response))
        return {"messages": messages, "structured_response": self.response}


@pytest.mark.asyncio
async def test_langgraph_react_web_agent_demo_flow(monkeypatch):
    from pathlib import Path
    from athos.models.enums import ExecutionMode
    from athos.models.flow import FlowInput
    from athos.models.session import FlowSession

    monkeypatch.setenv("CBORG_API_URL", "https://api.example.com")
    monkeypatch.setenv("CBORG_API_KEY", "dummy-key")

    cfg = build_config("config/config.yaml")

    flow_cfg = cfg.flows["langgraph_react_web_agent_demo"]
    assert flow_cfg.type == "langgraph_react_agent"
    assert flow_cfg.tools == ["langchain_tavily_search"]
    assert flow_cfg.max_iterations == 8

    class DummyModel:
        model_name = "test-model"

    dummy_model = DummyModel()
    dummy_tool = object()
    dummy_graph = DummyGraph("example search summary")
    create_calls = []

    def fake_build_model(model_cfg):
        return dummy_model

    def fake_build_tool(tool_cfg):
        return dummy_tool

    def fake_create_react_agent(model, tools, *, prompt=None):
        create_calls.append({"model": model, "tools": list(tools), "prompt": prompt})
        return dummy_graph

    monkeypatch.setattr(react_agent, "build_model", fake_build_model)
    monkeypatch.setattr(react_agent, "build_tool", fake_build_tool)
    monkeypatch.setattr(react_agent, "create_react_agent", fake_create_react_agent)

    flow = build_flow("langgraph_react_web_agent_demo", cfg)

    # Tools are built during initialize(), not during factory creation
    assert flow.tools == []
    assert flow.instructions is None

    # Initialize the flow (this builds tools and sets instructions)
    await flow.initialize(flow_cfg)

    assert flow.tools == [dummy_tool]
    assert flow.instructions is not None
    assert "web search tool" in flow.instructions

    # Create FlowInput with session
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
    assert result.content == "example search summary"

    assert create_calls == [
        {
            "model": dummy_model,
            "tools": [dummy_tool],
            "prompt": flow.instructions,
        }
    ]

    assert dummy_graph.invocations[0][1] == {"recursion_limit": 8}
