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
    command="servicenow-mcp",
    #command="python",
    #args=["-m", "athos.tools.servicenow_mcp.cli"],
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
tools = list(mcp_client.get_tools())

# Debugging
print("Available tools:")
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
    #print(f"  Inputs: {tool.inputs}")
    #print()
print()

# Get the tool I want to test
view_incident_logs = next(t for t in tools if t.name=="view_incident_logs")
print(view_incident_logs)

# Invoke the tool
result = view_incident_logs(limit=10, offset=0, state="", assigned_to="", category="", query="", incident_number="INC0247613", sys_id="")

print(f"Result: {result}")
