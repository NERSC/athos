from unittest.mock import Mock

import requests

from athos.tools.servicenow_mcp.auth.auth_manager import AuthManager
from athos.tools.servicenow_mcp.tools.user_tools import ListUsersParams, list_users
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


def test_list_users_success(monkeypatch):
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
                "department": {"display_value": "Engineering"},
                "manager": {"display_value": "Boss"},
                "phone": "555-0000",
                "mobile_phone": "555-1111",
                "location": {"display_value": "HQ"},
                "active": "true",
            },
            {
                "sys_id": "2",
                "user_name": "asmith",
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "asmith@example.com",
                "title": "Manager",
                "department": {"display_value": "HR"},
                "manager": {"display_value": "Director"},
                "phone": "555-2222",
                "mobile_phone": "555-3333",
                "location": {"display_value": "Branch"},
                "active": "false",
            },
        ]
    }
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)

    params = ListUsersParams(limit=5, offset=2)
    result = list_users(config, auth_manager, params)

    assert result == {
        "success": True,
        "message": "Retrieved 2 users",
        "users": [
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
                "active": True,
            },
            {
                "sys_id": "2",
                "user_name": "asmith",
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "asmith@example.com",
                "title": "Manager",
                "department": "HR",
                "manager": "Director",
                "phone": "555-2222",
                "mobile_phone": "555-3333",
                "location": "Branch",
                "active": False,
            },
        ],
        "total": 2,
        "limit": 5,
        "offset": 2,
    }


def test_list_users_empty(monkeypatch):
    config, auth_manager = _setup()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"result": []}
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)

    params = ListUsersParams()
    result = list_users(config, auth_manager, params)

    assert result == {
        "success": True,
        "message": "Retrieved 0 users",
        "users": [],
        "total": 0,
        "limit": 10,
        "offset": 0,
    }


def test_list_users_error(monkeypatch):
    config, auth_manager = _setup()

    def fake_get(*args, **kwargs):
        raise requests.exceptions.RequestException("boom")

    monkeypatch.setattr(requests, "get", fake_get)

    params = ListUsersParams()
    result = list_users(config, auth_manager, params)

    assert result["success"] is False
    assert result["users"] == []
    assert "Error listing users" in result["message"]
