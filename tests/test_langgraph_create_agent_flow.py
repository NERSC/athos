import pytest
from pathlib import Path

from athos.config.models import (
    AthosConfig,
    MCPServerConfig,
    MCPType,
    ModelConfig,
    ToolConfig,
    ToolFramework,
)
from athos.frameworks.langgraph.flows import create_agent as create_agent_module
from athos.frameworks.langgraph.flows.create_agent import (
    LangGraphCreateAgentFlow,
    LangGraphCreateAgentFlowConfig,
)
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput
from athos.models.session import FlowSession


class DummyGraph:
    def __init__(self, responses):
        self.responses = list(responses)
        self.invocations = []

    async def ainvoke(self, state, config=None):
        index = len(self.invocations)
        self.invocations.append((state, config))
        messages = list(state["messages"])
        response_text = (
            self.responses[index] if index < len(self.responses) else ""
        )
        messages.append(create_agent_module.AIMessage(response_text))
        return {"messages": messages}


@pytest.mark.asyncio
async def test_create_agent_flow_executes_and_tracks_history(monkeypatch):
    dummy_graph = DummyGraph(["first reply", "second reply"])
    create_calls = []

    def fake_create_agent(model, tools, *, system_prompt=None):
        create_calls.append(
            {
                "model": model,
                "tools": list(tools),
                "system_prompt": system_prompt,
            }
        )
        return dummy_graph

    monkeypatch.setattr(create_agent_module, "create_agent", fake_create_agent)

    class DummyModel:
        model_name = "test-model"

    def fake_build_model(cfg):
        return DummyModel()

    monkeypatch.setattr(create_agent_module, "build_model", fake_build_model)

    base_tool = object()

    full_cfg = AthosConfig(
        workspace_dir="/tmp",
        models={"test": ModelConfig(model_id="test-model")},
        tools={},
        mcp_servers={},
    )

    cfg = LangGraphCreateAgentFlowConfig(
        type="langgraph_create_agent",
        model="test",
        tools=[],
        instructions="Be concise.",
        max_iterations=7,
    )

    flow = await LangGraphCreateAgentFlow.create(cfg, full_cfg)
    flow.tools = [base_tool]

    session1 = FlowSession(
        session_id="test_session",
        user_id="test_user",
        workspace=Path("/tmp/test"),
    )
    session2 = FlowSession(
        session_id="test_session",
        user_id="test_user",
        workspace=Path("/tmp/test"),
    )

    input1 = FlowInput(
        message="Hello there",
        session=session1,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    first_result = await flow.execute(input1)

    session2.add_message("user", "Hello there")
    session2.add_message("assistant", first_result.content)

    input2 = FlowInput(
        message="How are you?",
        session=session2,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    second_result = await flow.execute(input2)

    assert first_result.content == "first reply"
    assert second_result.content == "second reply"

    assert len(create_calls) == 1
    assert create_calls[0]["system_prompt"] == "Be concise."
    assert create_calls[0]["tools"] == [base_tool]

    assert len(dummy_graph.invocations) == 2
    initial_state, initial_config = dummy_graph.invocations[0]
    followup_state, followup_config = dummy_graph.invocations[1]

    assert initial_config == {"recursion_limit": 7}
    assert followup_config == {"recursion_limit": 7}

    assert isinstance(initial_state["messages"][-1], create_agent_module.HumanMessage)
    assert initial_state["messages"][-1].content == "Hello there"

    assert [m.content for m in followup_state["messages"][:-1]] == [
        "Hello there",
        "first reply",
    ]
    assert followup_state["messages"][-1].content == "How are you?"


@pytest.mark.asyncio
async def test_create_agent_factory_combines_instructions_and_tools(monkeypatch):
    base_tool = object()
    mcp_tool = object()
    dummy_graph = DummyGraph(["combined response"])
    create_calls = []

    class DummyModel:
        model_name = "demo-model"

    def fake_build_model(model_cfg):
        assert model_cfg.model_id == "demo-model"
        return DummyModel()

    def fake_build_tool(tool_cfg):
        assert tool_cfg.callable_name == "DemoTool"
        return base_tool

    class DummyMCPClient:
        async def get_tools(self):
            return [mcp_tool]

        async def __aexit__(self, *args):
            pass

    def fake_build_mcp_client(name, mcp_cfg):
        assert name == "demo_mcp"
        assert mcp_cfg.mcp_type == MCPType.MCP_STDIO
        return DummyMCPClient()

    def fake_create_agent(model, tools, *, system_prompt=None):
        create_calls.append(
            {
                "model": model,
                "tools": list(tools),
                "system_prompt": system_prompt,
            }
        )
        return dummy_graph

    monkeypatch.setattr(create_agent_module, "build_model", fake_build_model)
    monkeypatch.setattr(create_agent_module, "build_tool", fake_build_tool)
    monkeypatch.setattr(create_agent_module, "build_mcp_client", fake_build_mcp_client)
    monkeypatch.setattr(create_agent_module, "create_agent", fake_create_agent)

    cfg = LangGraphCreateAgentFlowConfig(
        type="langgraph_create_agent",
        model="demo",
        tools=["demo_tool"],
        mcp_servers=["demo_mcp"],
        instructions="Primary instruction",
        max_iterations=3,
    )

    full_cfg = AthosConfig(
        workspace_dir="/tmp",
        models={"demo": ModelConfig(model_id="demo-model")},
        tools={
            "demo_tool": ToolConfig(
                callable_name="DemoTool",
                module_path="demo.module",
                parameters={},
                framework=ToolFramework.LANGGRAPH,
            )
        },
        mcp_servers={
            "demo_mcp": MCPServerConfig(
                mcp_type=MCPType.MCP_STDIO,
                command="echo",
                args=["hi"],
                instructions="Server instruction",
            )
        },
    )

    flow = await LangGraphCreateAgentFlow.create(cfg, full_cfg)

    assert flow.instructions == "Primary instruction\n\nServer instruction"

    session = FlowSession(
        session_id="test_session",
        user_id="test_user",
        workspace=Path("/tmp/test"),
    )

    input_data = FlowInput(
        message="Ping",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    result = await flow.execute(input_data)
    assert result.content == "combined response"
    assert result.metadata["model"] == "demo-model"

    assert len(create_calls) == 1
    assert create_calls[0]["system_prompt"] == "Primary instruction\n\nServer instruction"
    assert create_calls[0]["tools"] == [base_tool, mcp_tool]

    state, config = dummy_graph.invocations[0]
    assert config == {"recursion_limit": 3}
    assert isinstance(state["messages"][-1], create_agent_module.HumanMessage)
    assert state["messages"][-1].content == "Ping"
