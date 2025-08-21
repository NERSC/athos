"""Standalone testing of the ServiceNow MCP server using FastMCP.

This example mirrors ``sfapi_client_test.py`` and demonstrates how to invoke
tools on :class:`~athos.tools.servicenow_mcp.server.ServiceNowMCPServer` using
``fastmcp.Client`` without running a separate server process.
"""

import asyncio
import os
from dotenv import load_dotenv

from fastmcp import Client

from athos.tools.servicenow_mcp.server import ServiceNowMCPServer
from athos.tools.servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    ServerConfig,
)


async def main() -> None:
    """Create the server and call a couple of tools using ``Client``."""

    # Load environment variables from .env file
    load_dotenv()

    # Build server configuration using basic authentication
    auth_cfg = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(
            username=os.environ["SERVICENOW_USERNAME"],
            password=os.environ["SERVICENOW_PASSWORD"],
        ),
    )

    config = ServerConfig(
        instance_url=os.environ["SERVICENOW_INSTANCE_URL"],
        auth=auth_cfg,
    )

    # Instantiate the server object which holds a ``FastMCP`` instance
    server = ServiceNowMCPServer(config)

    # Point the FastMCP client at the server's ``mcp`` attribute
    client = Client(server.mcp)

    async with client:
        # Show all available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(" * ", tool, "\n")
        print()

        # Retrieve specific incident information
        incident_id = "INC0247762"
        incident_params = dict(incident_number=incident_id)
        incidents = await client.call_tool("list_incidents", incident_params)
        print("Incident info:", incidents)
        print()

        # Retrieve attachments
        incident_attachment_params = dict(incident_id=incident_id)
        attachments = await client.call_tool("get_incident_attachments", incident_attachment_params)
        print("Attachments:", attachments)
        print()

        # Download the attachment(s)
        attachment_sys_id = attachments.structured_content['attachments'][0]['sys_id']
        attachment_params = dict(attachment_sys_id=attachment_sys_id, download_dir="downloads")
        result = await client.call_tool("download_attachment", attachment_params)
        print(result)
        print()

    print("All done")

if __name__ == "__main__":
    asyncio.run(main())

