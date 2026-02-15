"""Standalone testing of the Chroma DB MCP"""

import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main() -> None:
    """Create the server and call a couple of tools using ``Client``."""

    # Load environment variables from .env file
    load_dotenv()

    data_dir = Path(os.environ["ATHOS_WORKSPACE"]) / "chroma"
    print(data_dir)

    # Configure the server
    transport = StdioTransport(
        #command="chroma-mcp",
        #args=["--client-type", "persistent", "--data-dir", str(data_dir)]
        command="uvx",
        args=["chroma-mcp", "--client-type", "persistent", "--data-dir", str(data_dir)]
    )

    # Construct the FastMCP client
    client = Client(transport)

    async with client:

        # Show all available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(" * ", tool, "\n")

        # List collections
        collections = await client.call_tool("chroma_list_collections", {"limit": "100", "offset": "0"})
        print(collections)
        # # Fetch the status of a specific system. This tool requires no auth.
        # status = await client.call_tool("get_system_status", {"system": "perlmutter"})
        # print("Perlmutter status:", status)

if __name__ == "__main__":
    asyncio.run(main())
