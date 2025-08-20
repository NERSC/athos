"""
Tools module for the ServiceNow MCP server.
"""

# Import tools as they are implemented
from .incident_tools import (
    add_comment,
    create_incident,
    list_incidents,
    resolve_incident,
    update_incident,
    view_incident_logs,
    get_incident_attachments,
)
from .user_tools import (
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
    "get_incident_attachments",
    
    # User lookup tools
    "get_user",
    "list_users",
]
