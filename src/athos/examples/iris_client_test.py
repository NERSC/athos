"""Standalone testing of the Iris GraphQL MCP server.

This example demonstrates how to use the FastMCP `Client` to invoke tools on
the Iris GraphQL MCP server without running a separate server process. The
approach mirrors the testing pattern used by the SFAPI example.
"""

import asyncio
from dotenv import load_dotenv
from fastmcp import Client

from athos.tools.iris_mcp import server as iris_server


async def main() -> None:
    """Create the server client and call a couple of tools using ``Client``."""

    # Load environment variables from .env file if present
    load_dotenv()

    # Configure the Iris client with values from the environment
    config = iris_server.load_config()
    iris_server.iris_client = iris_server.IrisGraphQLClient(config["base_url"])

    # Use FastMCP's Client to interact with the server's tools directly
    client = Client(iris_server.mcp)

    async with client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(" * ", tool, "\n")

        # Get user info by username
        user = await client.call_tool("get_user_info", {"username": "sfarrell"})
        print("User:", user.content[0].text)
        print()

        # Get project info by repository name
        project = await client.call_tool("get_project_info", {"pname": "m4291"})
        print("Project:", project.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())

