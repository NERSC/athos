import pytest
from pathlib import Path
from unittest.mock import MagicMock

from athos.tools.servicenow_mcp.auth.auth_manager import AuthManager
from athos.tools.servicenow_mcp.tools import incident_tools
from athos.tools.servicenow_mcp.tools.incident_tools import (
    DownloadAttachmentParams,
    download_attachment,
)
from athos.tools.servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    ServerConfig,
)


@pytest.mark.parametrize(
    "content_disposition,expected",
    [
        ('attachment; filename="log.txt"', "log.txt"),
        ("attachment; filename*=UTF-8''r%C3%A9sum%C3%A9.pdf", "résumé.pdf"),
    ],
)
def test_download_attachment(monkeypatch, tmp_path, content_disposition, expected):
    auth_cfg = AuthConfig(
        type=AuthType.BASIC, basic=BasicAuthConfig(username="u", password="p")
    )
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)

    binary_data = b"hello"
    mock_response = MagicMock()
    mock_response.headers = {"Content-Disposition": content_disposition}
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [binary_data]
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    mock_get = MagicMock(return_value=mock_response)
    monkeypatch.setattr(incident_tools.requests, "get", mock_get)

    monkeypatch.setenv("ATHOS_WORKSPACE", str(tmp_path))
    params = DownloadAttachmentParams(
        attachment_sys_id="att1"
    )
    result = download_attachment(config, auth_manager, params)

    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs.get("stream") is True
    assert mock_response.iter_content.called

    assert result["success"] is True
    file_path = Path(result["file_path"])
    assert file_path.exists()
    assert file_path.read_bytes() == binary_data
    assert file_path.name == expected
    assert file_path.parent == tmp_path / "attachments"

