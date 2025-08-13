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

        # Retrieve recent incidents
        incidents = await client.call_tool("list_incidents", {"limit": 1})
        print("Recent incidents:", incidents)


if __name__ == "__main__":
    asyncio.run(main())

