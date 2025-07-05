from typing import Any, Callable, Dict, Tuple, Type

# Import all necessary tool implementation functions and params models
# (This list needs to be kept complete and up-to-date)
from ..tools.incident_tools import (
    AddCommentParams,
    CreateIncidentParams,
    ListIncidentsParams,
    ResolveIncidentParams,
    UpdateIncidentParams,
    ViewIncidentLogsParams,
)
from ..tools.incident_tools import (
    add_comment as add_comment_tool,
)
from ..tools.incident_tools import (
    create_incident as create_incident_tool,
)
from ..tools.incident_tools import (
    list_incidents as list_incidents_tool,
)
from ..tools.incident_tools import (
    resolve_incident as resolve_incident_tool,
)
from ..tools.incident_tools import (
    update_incident as update_incident_tool,
)
from ..tools.incident_tools import (
    view_incident_logs as view_incident_logs_tool,
)
from ..tools.knowledge_base import (
    GetArticleParams,
    ListArticlesParams,
)
from ..tools.knowledge_base import (
    get_article as get_article_tool,
)
from ..tools.knowledge_base import (
    list_articles as list_articles_tool,
)
from ..tools.user_tools import (
    GetUserParams,
    ListUsersParams,
)
from ..tools.user_tools import (
    get_user as get_user_tool,
)
from ..tools.user_tools import (
    list_users as list_users_tool,
)

# Define a type alias for the Pydantic models or dataclasses used for params
ParamsModel = Type[Any]  # Use Type[Any] for broader compatibility initially

# Define the structure of the tool definition tuple
ToolDefinition = Tuple[
    Callable,  # Implementation function
    ParamsModel,  # Pydantic model for parameters
    Type,  # Return type annotation (used for hints, not strictly enforced by low-level server)
    str,  # Description
    str,  # Serialization method ('str', 'json', 'dict', 'model_dump', etc.)
]


def get_tool_definitions(
    create_kb_category_tool_impl: Callable = None, list_kb_categories_tool_impl: Callable = None
) -> Dict[str, ToolDefinition]:
    """
    Returns a dictionary containing definitions for all available ServiceNow tools.

    This centralizes the tool definitions for use in the server implementation.

    Returns:
        Dict[str, ToolDefinition]: A dictionary mapping tool names to their definitions.
    """
    tool_definitions: Dict[str, ToolDefinition] = {
        # Incident Tools
        "create_incident": (
            create_incident_tool,
            CreateIncidentParams,
            dict,  # Changed from str to dict for consistency
            "Create a new incident in ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the response data.",
            "json",  # Changed from str to json for consistent serialization
        ),
        "update_incident": (
            update_incident_tool,
            UpdateIncidentParams,
            dict,  # Changed from str to dict for consistency
            "Update an existing incident in ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the response data.",
            "json",  # Changed from str to json for consistent serialization
        ),
        "add_comment": (
            add_comment_tool,
            AddCommentParams,
            dict,  # Changed from str to dict for consistency
            "Add a comment to an incident in ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the response data.",
            "json",  # Changed from str to json for consistent serialization
        ),
        "view_incident_logs": (
            view_incident_logs_tool,
            ViewIncidentLogsParams,
            dict,  # Changed from str to dict for consistency
            "View the activity logs for an incident in ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the logs array.",
            "json",  # Tool returns list/dict
        ),
        "resolve_incident": (
            resolve_incident_tool,
            ResolveIncidentParams,
            dict,  # Changed from str to dict for consistency
            "Resolve an incident in ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the response data.",
            "json",  # Changed from str to json for consistent serialization
        ),
        "list_incidents": (
            list_incidents_tool,
            ListIncidentsParams,
            dict,  # Changed from str to dict for consistency
            "List incidents from ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the incidents array. The response contains success status, message, and incidents array.",
            "json",  # Tool returns list/dict, needs JSON dump
        ),
        # Knowledge Base Tools (lookup only)
        "list_articles": (
            list_articles_tool,
            ListArticlesParams,
            dict,  # Changed from Dict[str, Any] to dict for consistency
            "List knowledge articles. Returns a JSON string that must be parsed with json.loads() to access the articles array.",
            "json",  # Changed from raw_dict to json for consistent serialization
        ),
        "get_article": (
            get_article_tool,
            GetArticleParams,
            dict,  # Changed from Dict[str, Any] to dict for consistency
            "Get a specific knowledge article by ID. Returns a JSON string that must be parsed with json.loads() to access the article details.",
            "json",  # Changed from raw_dict to json for consistent serialization
        ),
        # User Tools (lookup only)
        "get_user": (
            get_user_tool,
            GetUserParams,
            dict,  # Changed from Dict[str, Any] to dict for consistency
            "Get a specific user in ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the user details.",
            "json",  # Changed from raw_dict to json for consistent serialization
        ),
        "list_users": (
            list_users_tool,
            ListUsersParams,
            dict,  # Changed from Dict[str, Any] to dict for consistency
            "List users in ServiceNow. Returns a JSON string that must be parsed with json.loads() to access the users array.",
            "json",  # Changed from raw_dict to json for consistent serialization
        ),
    }
    return tool_definitions
