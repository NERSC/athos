import pytest

from athos.tools.servicenow_mcp.server import ServiceNowMCPServer
from athos.tools.servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    ServerConfig,
)


@pytest.mark.asyncio
async def test_read_only_mode_disables_write_tools():
    auth_cfg = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(username="user", password="pass"),
    )
    config = ServerConfig(
        instance_url="https://example.service-now.com",
        auth=auth_cfg,
        read_only=True,
    )

    server = ServiceNowMCPServer(config)
    list_tools_fn = getattr(server.mcp, "list_tools", None)
    if list_tools_fn is None:
        list_tools_fn = server.mcp._list_tools
    tools = await list_tools_fn()
    tool_names = {tool.name for tool in tools}
    tools_by_name = {tool.name: tool for tool in tools}

    write_tools = {"create_incident", "update_incident", "add_comment", "resolve_incident"}
    for tool_name in write_tools:
        assert tool_name not in tool_names

    read_tools = {
        "list_incidents",
        "view_incident_logs",
        "get_incident_attachments",
        "download_attachment",
        "get_user",
        "list_users",
        "list_groups",
    }
    for tool_name in read_tools:
        assert tool_name in tool_names

    incident_tool = tools_by_name["list_incidents"]
    assert incident_tool.parameters["properties"]["sort"]["default"] == "created_desc"
    incident_params = incident_tool.parameters["properties"]
    assert "Do not pass encoded queries" in incident_params["query"]["description"]
    assert "list_groups" in incident_params["assignment_group"]["description"]

    group_tool = tools_by_name["list_groups"]
    assert group_tool.parameters["properties"]["active"]["default"] is True
    assert "list_incidents.assignment_group" in group_tool.description
