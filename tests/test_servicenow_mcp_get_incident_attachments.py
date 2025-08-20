from unittest.mock import Mock

from athos.tools.servicenow_mcp.auth.auth_manager import AuthManager
from athos.tools.servicenow_mcp.tools import incident_tools
from athos.tools.servicenow_mcp.tools.incident_tools import (
    GetIncidentAttachmentsParams,
    get_incident_attachments,
)
from athos.tools.servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    ServerConfig,
)


def test_get_incident_attachments(monkeypatch):
    auth_cfg = AuthConfig(
        type=AuthType.BASIC, basic=BasicAuthConfig(username="u", password="p")
    )
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)

    mock_response = Mock()
    mock_response.json.return_value = {
        "result": [
            {
                "sys_id": "att1",
                "file_name": "log.txt",
                "content_type": "text/plain",
                "size_bytes": "1234",
                "download_link": "https://example.com/att1",
            }
        ]
    }
    mock_response.raise_for_status.return_value = None

    monkeypatch.setattr(
        incident_tools.requests, "get", lambda *args, **kwargs: mock_response
    )

    params = GetIncidentAttachmentsParams(
        incident_id="1234567890abcdef1234567890abcdef"
    )
    result = get_incident_attachments(config, auth_manager, params)

    assert result["attachments"][0]["file_name"] == "log.txt"

