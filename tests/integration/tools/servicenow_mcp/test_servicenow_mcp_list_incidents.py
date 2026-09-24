from unittest.mock import Mock

import pytest
from pydantic import ValidationError

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


def test_list_incidents_sorts_by_most_recent_creation(monkeypatch):
    auth_cfg = AuthConfig(type=AuthType.BASIC, basic=BasicAuthConfig(username="u", password="p"))
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)

    mock_response = Mock()
    mock_response.json.return_value = {"result": []}
    mock_response.raise_for_status.return_value = None
    get = Mock(return_value=mock_response)
    monkeypatch.setattr(incident_tools.requests, "get", get)

    result = list_incidents(
        config,
        auth_manager,
        ListIncidentsParams(limit=3, sort="created_desc"),
    )

    assert result["success"] is True
    assert get.call_args.kwargs["params"]["sysparm_limit"] == 3
    assert (
        get.call_args.kwargs["params"]["sysparm_query"]
        == "ORDERBYDESCsys_created_on"
    )


def test_list_incidents_defaults_to_most_recent_creation(monkeypatch):
    auth_cfg = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(username="u", password="p"),
    )
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)

    mock_response = Mock()
    mock_response.json.return_value = {"result": []}
    mock_response.raise_for_status.return_value = None
    get = Mock(return_value=mock_response)
    monkeypatch.setattr(incident_tools.requests, "get", get)

    result = list_incidents(config, auth_manager, ListIncidentsParams(limit=3))

    assert result["sort"] == "created_desc"
    assert (
        get.call_args.kwargs["params"]["sysparm_query"]
        == "ORDERBYDESCsys_created_on"
    )


def test_list_incidents_filters_by_active_assignment_group(monkeypatch):
    auth_cfg = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(username="u", password="p"),
    )
    config = ServerConfig(instance_url="https://example.com", auth=auth_cfg)
    auth_manager = AuthManager(config.auth)

    mock_response = Mock()
    mock_response.json.return_value = {"result": []}
    mock_response.raise_for_status.return_value = None
    get = Mock(return_value=mock_response)
    monkeypatch.setattr(incident_tools.requests, "get", get)

    group_id = "0123456789abcdef0123456789abcdef"
    result = list_incidents(
        config,
        auth_manager,
        ListIncidentsParams(
            limit=10,
            active=True,
            assignment_group=group_id,
        ),
    )

    assert result["applied_filters"] == {
        "active": True,
        "assignment_group": group_id,
    }
    assert result["sort"] == "created_desc"
    assert (
        get.call_args.kwargs["params"]["sysparm_query"]
        == f"active=true^assignment_group={group_id}^ORDERBYDESCsys_created_on"
    )


def test_list_incidents_rejects_group_names_as_group_ids():
    with pytest.raises(ValidationError):
        ListIncidentsParams(assignment_group="DAS")


@pytest.mark.parametrize(
    "query",
    [
        "disk^NQactive=false",
        "disk^ORassignment_group=other",
    ],
)
def test_list_incidents_rejects_encoded_query_clauses(query):
    with pytest.raises(ValidationError, match="query must be plain text"):
        ListIncidentsParams(query=query)


def test_list_incidents_accepts_plain_text_query():
    params = ListIncidentsParams(query="disk failure on login node")

    assert params.query == "disk failure on login node"
