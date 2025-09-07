"""
Simple example demonstrating usage of the servicenow_mcp tool.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

from mcp import StdioServerParameters
from smolagents.mcp_client import MCPClient

import smolagents
print(smolagents)

# Load environment variables from .env file
load_dotenv()
data_dir = Path(os.environ["ATHOS_WORKSPACE"]) / "chroma"
print(data_dir)

# Connect to the running MCP server (stdio transport).
# For STDIO, smolagents will launch the process automatically.
mcp_params = StdioServerParameters(
    command="chroma-mcp",
    args=["--client-type", "persistent", "--data-dir", str(data_dir)]
    #command="uvx",
    #args=["chroma-mcp", "--client-type", "persistent", "--data-dir", str(data_dir)]
)

print("Constructing client")
print(MCPClient)
#mcp_client = MCPClient(mcp_params)
mcp_client = MCPClient(mcp_params, structured_output=True)
print(mcp_client)

# Gather tools exposed by the MCP server
tools = list(mcp_client.get_tools())

# Debugging
print("Available tools:")
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
    print(f"  Inputs: {tool.inputs}")
    print()
print()

# Get the tool I want to test
chroma_list_collections = next(t for t in tools if t.name=="chroma_list_collections")
print(chroma_list_collections)

# Invoke the tool
result = chroma_list_collections(limit=10, offset=0)
print(f"Result: {result}")
