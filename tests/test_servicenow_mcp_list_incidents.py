from unittest.mock import Mock

from athos.tools.servicenow_mcp.auth.auth_manager import AuthManager
from athos.tools.servicenow_mcp.tools import incident_tools
from athos.tools.servicenow_mcp.tools.incident_tools import ListIncidentsParams, list_incidents
from athos.tools.servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


def test_list_incidents_includes_assignment_group(monkeypatch):
    auth_cfg = AuthConfig(type=AuthType.BASIC, basic=BasicAuthConfig(username="u", password="p"))
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)

    mock_response = Mock()
    mock_response.json.return_value = {
        "result": [
            {
                "sys_id": "1",
                "number": "INC001",
                "short_description": "test",
                "description": "desc",
                "state": "1",
                "priority": "2",
                "assigned_to": {"display_value": "User"},
                "assignment_group": {"display_value": "Group1"},
                "category": "cat",
                "subcategory": "subcat",
                "sys_created_on": "2024-01-01",
                "sys_updated_on": "2024-01-02",
            }
        ]
    }
    mock_response.raise_for_status.return_value = None

    monkeypatch.setattr(incident_tools.requests, "get", lambda *args, **kwargs: mock_response)

    params = ListIncidentsParams()
    result = list_incidents(config, auth_manager, params)

    assert result["incidents"][0]["assignment_group"] == "Group1"
