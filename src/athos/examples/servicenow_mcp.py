"""
Simple example demonstrating usage of the servicenow_mcp tool.
"""

import os
from dotenv import load_dotenv

from mcp import StdioServerParameters
from smolagents.mcp_client import MCPClient

# Load environment variables from .env file
load_dotenv()

# Connect to the running MCP server (stdio transport).
# For STDIO, smolagents will launch the process automatically.
print("Constructing params")
mcp_params = StdioServerParameters(
    command="uv",
    args=["run", "python", "-m", "athos.tools.servicenow_mcp.cli"],
    env={
        "SERVICENOW_INSTANCE_URL": os.getenv("SERVICENOW_INSTANCE_URL"),
        "SERVICENOW_USERNAME": os.getenv("SERVICENOW_USERNAME"),
        "SERVICENOW_PASSWORD": os.getenv("SERVICENOW_PASSWORD"),
        "SERVICENOW_AUTH_TYPE": os.getenv("SERVICENOW_AUTH_TYPE")
    },
)

print("Constructing client")
mcp_client = MCPClient(mcp_params)
print(mcp_client)

# Gather tools exposed by the MCP server
print("Listing tools")
tools = list(mcp_client.get_tools())
print(tools)

# These tools can now be given to agent instances like CodeAgent, etc.