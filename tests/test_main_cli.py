import logging
import sys
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
    mock_runtime.assert_called_once_with("cfg.yaml")
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
    mock_runtime.assert_called_once_with("cfg.yaml")
    mock_build.assert_called_once_with("flow", "CFG")
    flow.execute.assert_called_once_with("hello")
    flow.close.assert_called_once_with()
