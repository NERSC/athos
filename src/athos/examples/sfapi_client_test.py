"""Standalone testing of the NERSC SuperFacility API MCP server.

This example demonstrates how to use the FastMCP `Client` to invoke tools on
`NERSCMCPServer` without running a separate server process.  The approach is
based on the FastMCP quickstart guide's testing instructions.
"""

import asyncio
from dotenv import load_dotenv
from fastmcp import Client

from athos.tools.sfapi_mcp.server import NERSCMCPServer, load_config


async def main() -> None:
    """Create the server and call a couple of tools using ``Client``."""

    # Load environment variables from .env file
    load_dotenv()

    # Instantiate the server object which holds a ``FastMCP`` instance
    config = load_config()
    server = NERSCMCPServer(
        client_id=config.get("client_id"),
        private_key=config.get("private_key"),
    )

    # Point the FastMCP client at the server's ``mcp`` attribute
    client = Client(server.mcp)

    async with client:

        # Show all available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(" * ", tool, "\n")

        # Fetch the status of a specific system. This tool requires no auth.
        status = await client.call_tool("get_system_status", {"system": "perlmutter"})
        print("Perlmutter status:", status)

        # # List all available systems for convenience
        # systems = await client.call_tool("get_available_systems", {})
        # print("Available systems:", systems)

        # Retrieve project information
        result = await client.call_tool("get_projects", {})
        print("Projects:", result)

    # Clean up HTTP resources used by the server
    await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
