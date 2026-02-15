from __future__ import annotations

import os
from pathlib import Path

import pytest


def _mcp_command_and_args(data_dir: str) -> tuple[str, list[str]]:
    """Build stdio command/args for chroma-mcp."""
    # Default to uvx so this matches runtime behavior used by lang_chroma_agent.
    cmd = os.getenv("ATHOS_CHROMA_MCP_CMD", "uvx")
    if cmd == "uvx":
        return cmd, [
            "chroma-mcp",
            "--client-type",
            "persistent",
            "--data-dir",
            data_dir,
        ]
    return cmd, [
        "--client-type",
        "persistent",
        "--data-dir",
        data_dir,
    ]


def _normalize_collections(payload) -> list[str]:
    """Normalize possible collection payloads to a sorted list of names."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return sorted(str(x) for x in payload)
    if isinstance(payload, dict):
        # Some wrappers may return {"collections": [...]} or similar structures.
        if "collections" in payload and isinstance(payload["collections"], list):
            return sorted(str(x) for x in payload["collections"])
        if "result" in payload and isinstance(payload["result"], list):
            return sorted(str(x) for x in payload["result"])
    return sorted([str(payload)])


@pytest.mark.skipif(
    os.getenv("ATHOS_CHROMA_INTEGRATION") != "1",
    reason="Set ATHOS_CHROMA_INTEGRATION=1 to run Chroma MCP adapter parity checks.",
)
def test_chroma_mcp_adapter_list_collections_parity():
    """Compare list_collections outputs for FastMCP vs SmolAgents MCP client.

    This is opt-in and uses a real local workspace DB.
    """
    workspace = Path(os.getenv("ATHOS_WORKSPACE", "/tmp/athos_workspace"))
    data_dir = str(workspace / "chroma")
    cmd, args = _mcp_command_and_args(data_dir)

    # FastMCP path
    import asyncio
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    async def _fastmcp_call():
        transport = StdioTransport(command=cmd, args=args)
        client = Client(transport)
        async with client:
            return await client.call_tool(
                "chroma_list_collections",
                {"limit": 100, "offset": 0},
            )

    fast_result = asyncio.run(_fastmcp_call())

    # Smol MCP adapter path
    from mcp import StdioServerParameters
    from smolagents.mcp_client import MCPClient

    params = StdioServerParameters(command=cmd, args=args)
    smol_client = MCPClient(params, structured_output=True)
    tools = list(smol_client.get_tools())
    list_tool = next(t for t in tools if t.name == "chroma_list_collections")
    smol_result = list_tool(limit=100, offset=0)

    fast_names = _normalize_collections(fast_result)
    smol_names = _normalize_collections(smol_result)
    assert smol_names == fast_names

