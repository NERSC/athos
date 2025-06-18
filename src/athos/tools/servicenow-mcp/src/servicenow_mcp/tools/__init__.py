"""
Tools module for the ServiceNow MCP server.
"""

# Import tools as they are implemented
from servicenow_mcp.tools.incident_tools import (
    add_comment,
    create_incident,
    list_incidents,
    resolve_incident,
    update_incident,
    view_incident_logs,
)
from servicenow_mcp.tools.knowledge_base import (
    get_article,
    list_articles,
)
from servicenow_mcp.tools.user_tools import (
    get_user,
    list_users,
)

__all__ = [
    # Incident tools
    "create_incident",
    "update_incident",
    "add_comment",
    "resolve_incident",
    "list_incidents",
    "view_incident_logs",
    
    # User lookup tools
    "get_user",
    "list_users",
    
    # Knowledge lookup tools
    "get_article",
    "list_articles",
] 