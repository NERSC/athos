import logging
import sys
from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock, Mock, patch

from athos.main import main


@pytest.mark.asyncio
@patch("athos.main.build_flow")
@patch("athos.main.build_config")
async def test_cli_log_level_override(mock_runtime, mock_build, monkeypatch):
    flow = AsyncMock()
    flow.execute.return_value = "OK"
    flow.close = Mock()
    mock_runtime.return_value = "CFG"
    mock_build.return_value = flow

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
    mock_runtime.assert_called_once_with("cfg.yaml", None)
    mock_build.assert_called_once_with("flow", "CFG")
    flow.execute.assert_called_once_with("hello")
    flow.close.assert_called_once_with()


@pytest.mark.asyncio
@patch("athos.main.build_flow")
@patch("athos.main.build_config")
async def test_cli_log_level_default(mock_runtime, mock_build, monkeypatch):
    flow = AsyncMock()
    flow.execute.return_value = "OK"
    flow.close = Mock()
    mock_runtime.return_value = "CFG"
    mock_build.return_value = flow

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
    mock_runtime.assert_called_once_with("cfg.yaml", None)
    mock_build.assert_called_once_with("flow", "CFG")
    flow.execute.assert_called_once_with("hello")
    flow.close.assert_called_once_with()


@pytest.mark.asyncio
@patch("athos.main.build_flow")
@patch("athos.main.build_config")
async def test_show_config(mock_runtime, mock_flow, monkeypatch, capsys):
    mock_runtime.return_value = SimpleNamespace(
        models={"m": SimpleNamespace(model_id="id")},
        tools={"t": SimpleNamespace(module_path="mod", callable_name="Tool")},
        mcp_servers={"s": SimpleNamespace(mcp_type="stdio")},
        flows={"f": SimpleNamespace(type="agent")},
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["athos.main", "--config", "cfg.yaml", "--show-config"],
    )

    result = await main()

    assert result == 0
    mock_runtime.assert_called_once_with("cfg.yaml", None)
    mock_flow.assert_not_called()
    captured = capsys.readouterr()
    assert "Models:" in captured.out
    assert "m: id" in captured.out
    assert "Tools:" in captured.out
    assert "MCP Servers:" in captured.out
    assert "Flows:" in captured.out


@pytest.mark.asyncio
@patch("athos.main.build_flow")
@patch("athos.main.build_config")
async def test_cli_set_override(mock_runtime, mock_build, monkeypatch):
    flow = AsyncMock()
    flow.execute.return_value = "OK"
    flow.close = Mock()
    mock_runtime.return_value = "CFG"
    mock_build.return_value = flow

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

    mock_runtime.assert_called_once_with(
        "cfg.yaml", {"models": {"test_model": {"temperature": 0.1, "max_tokens": 5}}}
    )
    mock_build.assert_called_once_with("flow", "CFG")
    flow.execute.assert_called_once_with("hello")
    flow.close.assert_called_once_with()
