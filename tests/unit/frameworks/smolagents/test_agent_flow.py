from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from athos.frameworks.smolagents.flows.agent import AgentFlow
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput
from athos.models.session import FlowSession


def _build_flow_with_mock_agent(monkeypatch):
    mock_agent = SimpleNamespace(
        run=Mock(return_value=SimpleNamespace(final_answer="ok")),
        tools=[],
    )
    monkeypatch.setattr(
        "athos.frameworks.smolagents.flows.agent.CodeAgent",
        lambda **_: mock_agent,
    )
    return AgentFlow(
        model=object(),
        tools=[],
        agent_type="code",
        mcp_clients=None,
        full_config=object(),
        max_steps=4,
        verbosity_level=0,
    ), mock_agent


@pytest.mark.asyncio
async def test_agent_flow_default_does_not_reset_memory(monkeypatch):
    flow, mock_agent = _build_flow_with_mock_agent(monkeypatch)
    flow_input = FlowInput(
        message="hello",
        session=FlowSession(session_id="s1", user_id="u1"),
        mode=ExecutionMode.SYNC,
    )

    await flow.execute(flow_input)

    mock_agent.run.assert_called_once_with(
        "hello",
        reset=False,
        return_full_result=True,
    )


@pytest.mark.asyncio
async def test_agent_flow_resets_memory_when_requested(monkeypatch):
    flow, mock_agent = _build_flow_with_mock_agent(monkeypatch)
    flow_input = FlowInput(
        message="hello",
        session=FlowSession(session_id="s2", user_id="u2"),
        mode=ExecutionMode.SYNC,
        metadata={"reset_agent_memory": True},
    )

    await flow.execute(flow_input)

    mock_agent.run.assert_called_once_with(
        "hello",
        reset=True,
        return_full_result=True,
    )


@pytest.mark.asyncio
async def test_agent_flow_includes_step_debug_metadata_when_requested(monkeypatch):
    flow, mock_agent = _build_flow_with_mock_agent(monkeypatch)
    mock_agent.run.return_value = SimpleNamespace(
        final_answer="ok",
        steps=[{"step_number": 1, "model_output": None}],
        state="max_steps_error",
    )
    flow_input = FlowInput(
        message="hello",
        session=FlowSession(session_id="s3", user_id="u3"),
        mode=ExecutionMode.SYNC,
        metadata={"debug_include_steps": True},
    )

    result = await flow.execute(flow_input)

    assert result.metadata["smolagent_steps"] == [{"step_number": 1, "model_output": None}]
    assert result.metadata["smolagent_state"] == "max_steps_error"


@pytest.mark.asyncio
async def test_agent_flow_logs_step_debug_at_verbose_level(monkeypatch, caplog):
    flow, mock_agent = _build_flow_with_mock_agent(monkeypatch)
    flow._verbosity_level = 2
    mock_agent.run.return_value = SimpleNamespace(
        final_answer="ok",
        steps=[
            {
                "step_number": 1,
                "model_output": None,
                "model_output_message": {"content": None, "tool_calls": [{"id": "t1"}]},
                "error": {"message": "parse error"},
            }
        ],
    )
    flow_input = FlowInput(
        message="hello",
        session=FlowSession(session_id="s4", user_id="u4"),
        mode=ExecutionMode.SYNC,
    )

    with caplog.at_level("INFO"):
        await flow.execute(flow_input)

    assert "smolagents step debug" in caplog.text
    assert '"step_number": 1' in caplog.text
