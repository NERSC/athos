import pytest
from types import SimpleNamespace

from athos.config.models import AthosConfig
from athos.frameworks.smolagents.flows import AgentFlow
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput
from athos.models.metrics import ExecutionMetrics
from athos.models.session import FlowSession


@pytest.mark.asyncio
async def test_smol_agent_flow_records_standard_metrics(tmp_path, monkeypatch):
    run_result = SimpleNamespace(
        output="done",
        token_usage=SimpleNamespace(input_tokens=120, output_tokens=45),
        steps=[
            SimpleNamespace(tool_calls=[SimpleNamespace(name="alpha"), SimpleNamespace(name="alpha")]),
            {"tool_calls": [{"function": {"name": "beta"}}, {"name": "gamma"}]},
        ],
    )

    class DummyAgent:
        def __init__(self, *, tools, model, **kwargs):
            self.tools = tools
            self.model = model

        def run(self, *args, **kwargs):
            return run_result

    monkeypatch.setattr("athos.frameworks.smolagents.flows.agent.CodeAgent", DummyAgent)

    flow = AgentFlow(
        model=SimpleNamespace(model_id="test-model"),
        tools=[],
        agent_type="code",
        mcp_clients=[],
        full_config=AthosConfig(workspace_dir=str(tmp_path)),
    )

    flow_input = FlowInput(
        message="Hello",
        session=FlowSession(session_id="s1", user_id="u1", workspace=tmp_path),
        mode=ExecutionMode.SYNC,
    )

    result = await flow.execute(flow_input)

    token_usage = result.metadata.get("token_usage")
    assert token_usage["input_tokens"] == 120
    assert token_usage["output_tokens"] == 45
    assert token_usage["total_tokens"] == 165

    tool_calls = {tc["name"]: tc["call_count"] for tc in result.metadata.get("tool_calls", [])}
    assert tool_calls == {"alpha": 2, "beta": 1, "gamma": 1}

    assert result.metadata.get("step_count") == 2

    metrics = ExecutionMetrics.from_metadata(result.metadata)
    assert metrics is not None
    assert metrics.token_usage.total_tokens == 165
    assert metrics.step_count == 2
    assert {tc.name for tc in metrics.tool_calls} == {"alpha", "beta", "gamma"}
