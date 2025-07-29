"""Standalone testing of the NERSC SuperFacility API MCP server.

This example demonstrates how to use the FastMCP `Client` to invoke tools on
`NERSCMCPServer` without running a separate server process.  The approach is
based on the FastMCP quickstart guide's testing instructions.
"""

import asyncio
from fastmcp import Client

from athos.tools.sfapi_mcp.server import NERSCMCPServer


async def main() -> None:
    """Create the server and call a couple of tools using ``Client``."""

    # Instantiate the server object which holds a ``FastMCP`` instance
    server = NERSCMCPServer()

    # Point the FastMCP client at the server's ``mcp`` attribute
    client = Client(server.mcp)

    async with client:
        # Fetch the status of a specific system. This tool requires no auth.
        status = await client.call_tool("get_system_status", {"system": "perlmutter"})
        print("Perlmutter status:", status)

        # List all available systems for convenience
        systems = await client.call_tool("get_available_systems", {})
        print("Available systems:", systems)

    # Clean up HTTP resources used by the server
    await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
