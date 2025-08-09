#!/usr/bin/env python3
"""MCP server providing BM25-based retrieval over NERSC docs."""

import argparse
import asyncio
from pathlib import Path
from typing import List

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import mcp.types as types

from .rag_bm25 import RAGBM25

REPO_URL = "https://gitlab.com/NERSC/nersc.gitlab.io.git"
LOCAL_PATH = Path(__file__).resolve().parent / "nersc_docs"

server = Server("rag-mcp-server")
rag_index: RAGBM25 | None = None


@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="query",
            description="Search NERSC documentation using BM25",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    if name != "query":
        raise ValueError(f"Unknown tool: {name}")
    query = str(arguments.get("query", ""))
    k = int(arguments.get("k", 5))
    if not query:
        return [types.TextContent(type="text", text="Empty query")] 
    if rag_index is None:
        return [types.TextContent(type="text", text="Index not ready")]
    results = rag_index.query(query, k=k)
    texts = [f"{path}: {chunk}" for path, chunk in results]
    return [types.TextContent(type="text", text="\n\n".join(texts))]


async def main() -> None:
    global rag_index
    parser = argparse.ArgumentParser(description="RAG MCP Server")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index")
    args = parser.parse_args()

    if args.rebuild and LOCAL_PATH.exists():
        import shutil

        shutil.rmtree(LOCAL_PATH)

    rag_index = RAGBM25.from_repo(REPO_URL, str(LOCAL_PATH))

    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="rag-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
