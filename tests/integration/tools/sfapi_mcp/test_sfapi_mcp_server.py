from unittest.mock import AsyncMock, Mock
import pytest

from athos.tools.sfapi_mcp.server import NERSCMCPServer, load_config


def test_load_config_env(monkeypatch, tmp_path):
    key_file = tmp_path / "key.pem"
    key_file.write_text("PRIVATEKEY")
    monkeypatch.setenv("NERSC_CLIENT_ID", "client123")
    monkeypatch.setenv("NERSC_PRIVATE_KEY_PATH", str(key_file))
    cfg = load_config()
    assert cfg["client_id"] == "client123"
    assert cfg["private_key"] == "PRIVATEKEY"


@pytest.mark.asyncio
async def test_list_directory_without_auth():
    server = NERSCMCPServer()
    tool = await server.mcp.get_tool("list_directory")
    result = await tool.run({"system": "perlmutter", "path": "/"})
    assert result.structured_content["type"] == "authentication_required"
    assert "Authentication not configured" in result.structured_content["error"]


def test_handle_error_authentication():
    server = NERSCMCPServer()
    result = server._handle_error(Exception("401 Unauthorized"))
    assert result["type"] == "authentication_error"


@pytest.mark.asyncio
async def test_get_system_status(monkeypatch):
    from athos.tools.sfapi_mcp import server as server_module

    mock_response = Mock()
    mock_response.json.return_value = {"status": "up"}
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return mock_client

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(server_module.httpx, "AsyncClient", DummyClient)

    server = NERSCMCPServer()
    tool = await server.mcp.get_tool("get_system_status")
    result = await tool.run({"system": "perlmutter"})
    assert result.structured_content == {"status": "up"}
    mock_client.get.assert_called_once_with(
        "https://api.nersc.gov/api/v1.2/status/perlmutter"
    )


@pytest.mark.asyncio
async def test_get_system_status_wraps_list(monkeypatch):
    from athos.tools.sfapi_mcp import server as server_module

    mock_response = Mock()
    mock_response.json.return_value = [{"name": "perlmutter"}]
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return mock_client

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(server_module.httpx, "AsyncClient", DummyClient)

    server = NERSCMCPServer()
    tool = await server.mcp.get_tool("get_system_status")
    result = await tool.run({})
    assert result.structured_content == {"systems": [{"name": "perlmutter"}]}
    mock_client.get.assert_called_once_with("https://api.nersc.gov/api/v1.2/status")
