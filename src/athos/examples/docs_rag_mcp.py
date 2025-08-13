"""Standalone testing of the documentation RAG MCP server using FastMCP.

This example mirrors other MCP test scripts and demonstrates how to invoke
:class:`~athos.tools.rag_mcp.rag_mcp_server.RAGMCPServer` tools using
:class:`fastmcp.Client` without running a separate server process.
"""

import asyncio

from fastmcp import Client

from athos.tools.rag_mcp.rag_mcp_server import RAGMCPServer


async def main() -> None:
    """Create the server, build the index and query the docs."""

    # Instantiate the server object which holds a ``FastMCP`` instance
    server = RAGMCPServer()
    server.build_index()

    # Point the FastMCP client at the server's ``mcp`` attribute
    client = Client(server.mcp)

    async with client:
        # Show all available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(" * ", tool, "\n")

        # Perform a simple query
        results = await client.call_tool(
            "query",
            {"query": "How can I run pytorch workloads at NERSC?", "k": 3},
        )
        print("Query results:\n", results)


if __name__ == "__main__":
    asyncio.run(main())
