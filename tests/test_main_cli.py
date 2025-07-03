import logging
import sys
import pytest
from unittest.mock import AsyncMock, patch

from athos.main import main


@pytest.mark.asyncio
@patch('athos.main.create_athos_manager')
async def test_cli_log_level_override(mock_create, monkeypatch):
    mgr = AsyncMock()
    mgr.execute_flow.return_value = "OK"
    mock_create.return_value = mgr

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    monkeypatch.setattr(sys, "argv", [
        "athos.main",
        "--config",
        "cfg.yaml",
        "--flow",
        "flow",
        "--input",
        "hello",
        "--log-level",
        "DEBUG",
    ])

    await main()

    assert root_logger.level == logging.DEBUG
    mock_create.assert_called_once_with("cfg.yaml")
    mgr.execute_flow.assert_called_once_with("flow", "hello")


@pytest.mark.asyncio
@patch('athos.main.create_athos_manager')
async def test_cli_log_level_default(mock_create, monkeypatch):
    mgr = AsyncMock()
    mgr.execute_flow.return_value = "OK"
    mock_create.return_value = mgr

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    monkeypatch.setattr(sys, "argv", [
        "athos.main",
        "--config",
        "cfg.yaml",
        "--flow",
        "flow",
        "--input",
        "hello",
    ])

    await main()

    assert root_logger.level == logging.WARNING
    mock_create.assert_called_once_with("cfg.yaml")
    mgr.execute_flow.assert_called_once_with("flow", "hello")

