import logging
import sys
from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock, Mock, patch

from athos.main import main
from athos.models.execution import FlowResult
from athos.models.flow import FlowOutput


@pytest.mark.asyncio
@patch("athos.main.FlowRunner")
@patch("athos.main.build_config")
async def test_cli_log_level_override(mock_build_config, mock_flow_runner, monkeypatch):
    mock_build_config.return_value = "CFG"
    mock_runner_instance = AsyncMock()
    mock_runner_instance.execute.return_value = FlowResult(
        success=True, output=FlowOutput(content="OK", artifacts=[]), request_id="123", session_id="cli_session", execution_time=0.5
    )
    mock_flow_runner.return_value = mock_runner_instance

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "athos.main",
            "--config",
            "cfg.yaml",
            "--flow",
            "flow",
            "--input",
            "hello",
            "--log-level",
            "DEBUG",
        ],
    )

    await main()

    assert root_logger.level == logging.DEBUG
    mock_build_config.assert_called_once_with("cfg.yaml", None)
    mock_flow_runner.assert_called_once_with("CFG")
    mock_runner_instance.execute.assert_called_once_with(
        flow_name="flow",
        message="hello",
        session_id="cli_session",
        user_id="cli_user",
        interface="cli",
        metadata={"cli": True},
    )
    mock_runner_instance.cleanup.assert_called_once_with()


@pytest.mark.asyncio
@patch("athos.main.FlowRunner")
@patch("athos.main.build_config")
async def test_cli_log_level_default(mock_build_config, mock_flow_runner, monkeypatch):
    mock_build_config.return_value = "CFG"
    mock_runner_instance = AsyncMock()
    mock_runner_instance.execute.return_value = FlowResult(
        success=True, output=FlowOutput(content="OK", artifacts=[]), request_id="123", session_id="cli_session", execution_time=0.5
    )
    mock_flow_runner.return_value = mock_runner_instance

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "athos.main",
            "--config",
            "cfg.yaml",
            "--flow",
            "flow",
            "--input",
            "hello",
        ],
    )

    await main()

    assert root_logger.level == logging.WARNING
    mock_build_config.assert_called_once_with("cfg.yaml", None)
    mock_flow_runner.assert_called_once_with("CFG")
    mock_runner_instance.execute.assert_called_once_with(
        flow_name="flow",
        message="hello",
        session_id="cli_session",
        user_id="cli_user",
        interface="cli",
        metadata={"cli": True},
    )
    mock_runner_instance.cleanup.assert_called_once_with()


@pytest.mark.asyncio
@patch("athos.main.build_flow")
@patch("athos.main.build_config")
async def test_show_config(mock_build_config, mock_build_flow, monkeypatch, capsys):
    mock_build_config.return_value = SimpleNamespace(
        models={
            "m": SimpleNamespace(model_id="id", description="Model description"),
        },
        tools={
            "t": SimpleNamespace(
                module_path="mod",
                callable_name="Tool",
                description="Tool description",
            )
        },
        mcp_servers={
            "s": SimpleNamespace(mcp_type="stdio", description="MCP description"),
        },
        flows={
            "f": SimpleNamespace(
                type="agent",
                model="m",
                description="Flow description",
            )
        },
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["athos.main", "--config", "cfg.yaml", "--show-config"],
    )

    await main()

    mock_build_config.assert_called_once_with("cfg.yaml", None)
    mock_build_flow.assert_not_called()
    captured = capsys.readouterr()
    assert "Models:" in captured.out
    assert "m: id" in captured.out
    assert "Description: Model description" in captured.out
    assert "Tools:" in captured.out
    assert "Description: Tool description" in captured.out
    assert "MCP Servers:" in captured.out
    assert "Description: MCP description" in captured.out
    assert "Flows:" in captured.out
    assert "agent (model=m)" in captured.out
    assert "Description: Flow description" in captured.out


@pytest.mark.asyncio
@patch("athos.main.FlowRunner")
@patch("athos.main.build_config")
async def test_cli_set_override(mock_build_config, mock_flow_runner, monkeypatch):
    mock_build_config.return_value = "CFG"
    mock_runner_instance = AsyncMock()
    mock_runner_instance.execute.return_value = FlowResult(
        success=True, output=FlowOutput(content="OK", artifacts=[]), request_id="123", session_id="cli_session", execution_time=0.5
    )
    mock_flow_runner.return_value = mock_runner_instance

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "athos.main",
            "--config",
            "cfg.yaml",
            "--flow",
            "flow",
            "--input",
            "hello",
            "--set",
            "models.test_model.temperature=0.1",
            "--set",
            "models.test_model.max_tokens=5",
        ],
    )

    await main()

    mock_build_config.assert_called_once_with(
        "cfg.yaml", {"models": {"test_model": {"temperature": 0.1, "max_tokens": 5}}}
    )
    mock_flow_runner.assert_called_once_with("CFG")
    mock_runner_instance.execute.assert_called_once_with(
        flow_name="flow",
        message="hello",
        session_id="cli_session",
        user_id="cli_user",
        interface="cli",
        metadata={"cli": True},
    )
    mock_runner_instance.cleanup.assert_called_once_with()


@pytest.mark.asyncio
@patch("athos.runtime.runner.build_flow")
@patch("athos.main.build_config")
async def test_gradio_keyboard_interrupt(mock_build_config, mock_build_flow, monkeypatch, caplog):
    from athos.config.models import ToolFramework
    flow = SimpleNamespace(agent="agent", cleanup=AsyncMock(), framework=ToolFramework.SMOLAGENTS)
    mock_build_flow.return_value = flow
    mock_build_config.return_value = SimpleNamespace(
        flows={"flow": SimpleNamespace(type="agent")}
    )

    class DummyUI:
        def __init__(self, agent):
            pass

        def launch(self, *args, **kwargs):
            raise KeyboardInterrupt()

    monkeypatch.setattr(sys, "argv", ["athos.main", "--config", "cfg.yaml", "--flow", "flow", "--gradio"])
    monkeypatch.setattr("athos.main.GradioUI", DummyUI)

    with caplog.at_level(logging.INFO):
        await main()

    assert "Gradio server stopped by user" in caplog.text
    flow.cleanup.assert_called_once_with()
