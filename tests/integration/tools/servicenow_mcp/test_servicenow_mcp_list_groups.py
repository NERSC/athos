from unittest.mock import Mock

import pytest
import requests
from pydantic import ValidationError

from athos.tools.servicenow_mcp.auth.auth_manager import AuthManager
from athos.tools.servicenow_mcp.tools import group_tools
from athos.tools.servicenow_mcp.tools.group_tools import ListGroupsParams, list_groups
from athos.tools.servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    ServerConfig,
)


def _setup():
    auth_cfg = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(username="u", password="p"),
    )
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    return config, AuthManager(config.auth)


def test_list_groups_resolves_active_group_names(monkeypatch):
    config, auth_manager = _setup()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "result": [
            {
                "sys_id": "0123456789abcdef0123456789abcdef",
                "name": "DAS",
                "description": "Data and Analytics Services",
                "active": "true",
                "manager": {"display_value": "Manager Name"},
                "parent": "",
            }
        ]
    }
    get = Mock(return_value=mock_response)
    monkeypatch.setattr(group_tools.requests, "get", get)

    result = list_groups(
        config,
        auth_manager,
        ListGroupsParams(query="DAS"),
    )

    assert result["groups"] == [
        {
            "sys_id": "0123456789abcdef0123456789abcdef",
            "name": "DAS",
            "description": "Data and Analytics Services",
            "active": True,
            "manager": "Manager Name",
            "parent": "",
        }
    ]
    assert result["applied_filters"] == {"active": True, "query": "DAS"}
    assert result["sort"] == "name_asc"
    assert get.call_args.args[0] == "https://example.com/api/now/table/sys_user_group"
    assert (
        get.call_args.kwargs["params"]["sysparm_query"]
        == "active=true^nameLIKEDAS^ORDERBYname"
    )


def test_list_groups_can_include_inactive_groups(monkeypatch):
    config, auth_manager = _setup()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"result": []}
    get = Mock(return_value=mock_response)
    monkeypatch.setattr(group_tools.requests, "get", get)

    result = list_groups(
        config,
        auth_manager,
        ListGroupsParams(active=None),
    )

    assert result["applied_filters"] == {}
    assert get.call_args.kwargs["params"]["sysparm_query"] == "ORDERBYname"


@pytest.mark.parametrize(
    "query",
    [
        "DAS^NQactive=false",
        "DAS^ORactive=false",
    ],
)
def test_list_groups_rejects_encoded_query_clauses(query):
    with pytest.raises(ValidationError, match="query must be plain text"):
        ListGroupsParams(query=query)


def test_list_groups_accepts_plain_text_with_spaces():
    params = ListGroupsParams(query="Data and Analytics Services")

    assert params.query == "Data and Analytics Services"


def test_list_groups_handles_request_errors(monkeypatch):
    config, auth_manager = _setup()

    def fail(*args, **kwargs):
        raise requests.exceptions.RequestException("boom")

    monkeypatch.setattr(group_tools.requests, "get", fail)

    result = list_groups(config, auth_manager, ListGroupsParams(query="DAS"))

    assert result["success"] is False
    assert result["groups"] == []
    assert "Error listing groups" in result["message"]
