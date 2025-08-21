from pathlib import Path
from unittest.mock import Mock

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


def test_download_attachment(monkeypatch, tmp_path):
    auth_cfg = AuthConfig(
        type=AuthType.BASIC, basic=BasicAuthConfig(username="u", password="p")
    )
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)

    binary_data = b"hello"
    mock_response = Mock()
    mock_response.content = binary_data
    mock_response.headers = {"Content-Disposition": 'attachment; filename="log.txt"'}
    mock_response.raise_for_status.return_value = None

    monkeypatch.setattr(
        incident_tools.requests, "get", lambda *args, **kwargs: mock_response
    )

    params = DownloadAttachmentParams(
        attachment_sys_id="att1", download_dir=str(tmp_path)
    )
    result = download_attachment(config, auth_manager, params)

    assert result["success"] is True
    file_path = Path(result["file_path"])
    assert file_path.exists()
    assert file_path.read_bytes() == binary_data
