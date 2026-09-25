from unittest.mock import Mock

import requests

from athos.tools.servicenow_mcp.auth.auth_manager import AuthManager
from athos.tools.servicenow_mcp.tools.user_tools import GetUserParams, get_user
from athos.tools.servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    ServerConfig,
)


def _setup():
    auth_cfg = AuthConfig(
        type=AuthType.BASIC, basic=BasicAuthConfig(username="u", password="p")
    )
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)
    return config, auth_manager


def test_get_user_success(monkeypatch):
    config, auth_manager = _setup()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "result": [
            {
                "sys_id": "1",
                "user_name": "jdoe",
                "first_name": "John",
                "last_name": "Doe",
                "email": "jdoe@example.com",
                "title": "Developer",
                "department": "Engineering",
                "manager": "Boss",
                "phone": "555-0000",
                "mobile_phone": "555-1111",
                "location": "HQ",
                "active": "true",
            }
        ]
    }
    get = Mock(return_value=mock_response)
    monkeypatch.setattr(requests, "get", get)

    params = GetUserParams(user_id="1")
    result = get_user(config, auth_manager, params)

    assert result == {
        "success": True,
        "message": "User retrieved successfully",
        "user": {
            "sys_id": "1",
            "user_name": "jdoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "jdoe@example.com",
            "title": "Developer",
            "department": "Engineering",
            "manager": "Boss",
            "phone": "555-0000",
            "mobile_phone": "555-1111",
            "location": "HQ",
            "active": True,
        },
    }
    assert get.call_args.kwargs["params"] == {
        "sysparm_query": "sys_id=1",
        "sysparm_limit": 1,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }


def test_get_user_not_found(monkeypatch):
    config, auth_manager = _setup()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"result": []}
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)

    params = GetUserParams(user_id="missing")
    result = get_user(config, auth_manager, params)

    assert result == {
        "success": False,
        "message": "User not found",
        "user": None,
    }


def test_get_user_error(monkeypatch):
    config, auth_manager = _setup()

    def fake_get(*args, **kwargs):
        raise requests.exceptions.RequestException("boom")

    monkeypatch.setattr(requests, "get", fake_get)

    params = GetUserParams(user_id="1")
    result = get_user(config, auth_manager, params)

    assert result["success"] is False
    assert result["user"] is None
    assert "Error retrieving user" in result["message"]
