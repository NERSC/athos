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
from athos.frameworks.langgraph.flows import agent as agent_module
from athos.frameworks.langgraph.flows.agent import (
    LangChainAgentFlow,
    LangChainAgentFlowConfig,
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
        messages.append(agent_module.AIMessage(response_text))
        return {"messages": messages}


@pytest.mark.asyncio
async def test_agent_flow_executes_and_tracks_history(monkeypatch):
    dummy_graph = DummyGraph(["first reply", "second reply"])
    create_calls = []

    def fake_create_agent(model, tools, *, system_prompt=None, checkpointer=None):
        create_calls.append(
            {
                "model": model,
                "tools": list(tools),
                "system_prompt": system_prompt,
                "checkpointer": checkpointer,
            }
        )
        return dummy_graph

    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)

    class DummyModel:
        model_name = "test-model"

    def fake_build_model(cfg):
        return DummyModel()

    monkeypatch.setattr(agent_module, "build_model", fake_build_model)

    base_tool = object()

    full_cfg = AthosConfig(
        workspace_dir="/tmp",
        models={"test": ModelConfig(model_id="test-model")},
        tools={},
        mcp_servers={},
    )

    cfg = LangChainAgentFlowConfig(
        type="langchain_agent",
        model="test",
        tools=[],
        system_prompt="Be concise.",
        max_iterations=7,
    )

    flow = await LangChainAgentFlow.create(cfg, full_cfg)
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

    assert initial_config == {
        "configurable": {"thread_id": "test_session"},
        "recursion_limit": 7
    }
    assert followup_config == {
        "configurable": {"thread_id": "test_session"},
        "recursion_limit": 7
    }

    # With checkpointing, only the new message is passed
    assert len(initial_state["messages"]) == 1
    assert isinstance(initial_state["messages"][0], agent_module.HumanMessage)
    assert initial_state["messages"][0].content == "Hello there"

    # Second invocation also only gets the new message (checkpoint handles history)
    assert len(followup_state["messages"]) == 1
    assert isinstance(followup_state["messages"][0], agent_module.HumanMessage)
    assert followup_state["messages"][0].content == "How are you?"


@pytest.mark.asyncio
async def test_agent_factory_combines_instructions_and_tools(monkeypatch):
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

    def fake_create_agent(model, tools, *, system_prompt=None, checkpointer=None):
        create_calls.append(
            {
                "model": model,
                "tools": list(tools),
                "system_prompt": system_prompt,
                "checkpointer": checkpointer,
            }
        )
        return dummy_graph

    monkeypatch.setattr(agent_module, "build_model", fake_build_model)
    monkeypatch.setattr(agent_module, "build_tool", fake_build_tool)
    monkeypatch.setattr(agent_module, "build_mcp_client", fake_build_mcp_client)
    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)

    cfg = LangChainAgentFlowConfig(
        type="langchain_agent",
        model="demo",
        tools=["demo_tool"],
        mcp_servers=["demo_mcp"],
        system_prompt="Primary instruction",
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

    flow = await LangChainAgentFlow.create(cfg, full_cfg)

    assert flow.system_prompt == "Primary instruction\n\nServer instruction"

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
    assert config == {
        "configurable": {"thread_id": "test_session"},
        "recursion_limit": 3
    }
    assert isinstance(state["messages"][-1], agent_module.HumanMessage)
    assert state["messages"][-1].content == "Ping"


@pytest.mark.asyncio
async def test_agent_flow_emits_standardized_metrics(monkeypatch):
    metrics_graph_invocations = []

    class MetricsDummyGraph:
        async def ainvoke(self, state, config=None):
            metrics_graph_invocations.append((state, config))
            messages = list(state["messages"])

            # Simulate an AI message with token usage and tool calls
            usage_metadata = type("Usage", (), {"input_tokens": 12, "output_tokens": 34})()
            ai_message = agent_module.AIMessage(content="Metrics response")
            ai_message.usage_metadata = usage_metadata
            ai_message.tool_calls = [{"name": "search"}]

            messages.append(ai_message)
            return {"messages": messages}

    def fake_create_agent(model, tools, *, system_prompt=None, checkpointer=None):
        return MetricsDummyGraph()

    class DummyModel:
        model_name = "metrics-model"

    monkeypatch.setattr(agent_module, "build_model", lambda cfg: DummyModel())
    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)

    cfg = LangChainAgentFlowConfig(
        type="langchain_agent",
        model="metrics",
        tools=[],
        mcp_servers=[],
        system_prompt=None,
        max_iterations=2,
    )

    full_cfg = AthosConfig(
        workspace_dir="/tmp",
        models={"metrics": ModelConfig(model_id="metrics-model")},
        tools={},
        mcp_servers={},
    )

    flow = await LangChainAgentFlow.create(cfg, full_cfg)

    session = FlowSession(
        session_id="metrics_session",
        user_id="metrics_user",
        workspace=Path("/tmp/test"),
    )

    input_data = FlowInput(
        message="Measure tokens",
        session=session,
        mode=ExecutionMode.SYNC,
        metadata={},
    )

    result = await flow.execute(input_data)

    assert result.metadata["token_usage"] == {
        "input_tokens": 12,
        "output_tokens": 34,
        "total_tokens": 46,
    }
    assert result.metadata["tool_calls"] == [{"name": "search", "call_count": 1}]
    assert result.metadata["step_count"] == 1

    # Ensure the invocation used the expected config/thread_id
    assert metrics_graph_invocations[0][1] == {
        "configurable": {"thread_id": "metrics_session"},
        "recursion_limit": 2
    }


@pytest.mark.asyncio
async def test_agent_handles_optional_dependencies(monkeypatch):
    monkeypatch.setattr(agent_module, "create_agent", None)
    monkeypatch.setattr(agent_module, "_CREATE_AGENT_IMPORT_ERROR", ImportError("boom"))

    class DummyModel:
        model_name = "demo-model"

    monkeypatch.setattr(agent_module, "build_model", lambda cfg: DummyModel())

    cfg = LangChainAgentFlowConfig(
        type="langchain_agent",
        model="demo",
        tools=[],
        mcp_servers=[],
        system_prompt=None,
        max_iterations=1,
    )

    full_cfg = AthosConfig(
        workspace_dir="/tmp",
        models={"demo": ModelConfig(model_id="demo-model")},
        tools={},
        mcp_servers={},
    )

    with pytest.raises(ImportError):
        flow = await LangChainAgentFlow.create(cfg, full_cfg)
        await flow.execute(
            FlowInput(
                message="test",
                session=FlowSession(
                    session_id="s",
                    user_id="u",
                    workspace=Path("/tmp"),
                ),
                mode=ExecutionMode.SYNC,
                metadata={},
            )
        )
