"""
User lookup tools for the ServiceNow MCP server.

This module provides tools for looking up users in ServiceNow.
"""

import logging
from typing import Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class GetUserParams(BaseModel):
    """Parameters for getting a user."""

    user_id: Optional[str] = Field(None, description="User ID or sys_id")
    user_name: Optional[str] = Field(None, description="Username of the user")
    email: Optional[str] = Field(None, description="Email address of the user")


class ListUsersParams(BaseModel):
    """Parameters for listing users."""

    limit: int = Field(10, description="Maximum number of users to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    department: Optional[str] = Field(None, description="Filter by department")
    query: Optional[str] = Field(
        None,
        description="Case-insensitive search term that matches against name, username, or email fields. Uses ServiceNow's LIKE operator for partial matching.",
    )


def get_user(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUserParams,
) -> dict:
    """
    Get a user from ServiceNow by user ID, username, or email.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting the user.

    Returns:
        Dictionary containing user details.
    """
    if not any([params.user_id, params.user_name, params.email]):
        raise ValueError("At least one of user_id, user_name, or email must be provided")

    api_url = f"{config.api_url}/table/sys_user"

    # Build query
    query_parts = []
    if params.user_id:
        query_parts.append(f"sys_id={params.user_id}")
    if params.user_name:
        query_parts.append(f"user_name={params.user_name}")
    if params.email:
        query_parts.append(f"email={params.email}")

    query = "^OR".join(query_parts)

    params_dict = {"sysparm_query": query, "sysparm_limit": 1}

    try:
        response = requests.get(
            api_url,
            params=params_dict,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json()
        users = result.get("result", [])

        if not users:
            return {"success": False, "message": "User not found", "user": None}

        user = users[0]
        return {
            "success": True,
            "message": "User retrieved successfully",
            "user": {
                "sys_id": user.get("sys_id"),
                "user_name": user.get("user_name"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "email": user.get("email"),
                "title": user.get("title"),
                "department": user.get("department", {}).get("display_value"),
                "manager": user.get("manager", {}).get("display_value"),
                "phone": user.get("phone"),
                "mobile_phone": user.get("mobile_phone"),
                "location": user.get("location", {}).get("display_value"),
                "active": user.get("active") == "true",
            },
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving user: {str(e)}")
        return {"success": False, "message": f"Error retrieving user: {str(e)}", "user": None}


def list_users(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUsersParams,
) -> dict:
    """
    List users from ServiceNow with optional filtering.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing users.

    Returns:
        Dictionary containing list of users.
    """
    api_url = f"{config.api_url}/table/sys_user"

    # Build query
    query_parts = []

    if params.active is not None:
        query_parts.append(f"active={str(params.active).lower()}")

    if params.department:
        query_parts.append(f"department.nameLIKE{params.department}")

    if params.query:
        # Search across multiple fields
        search_query = (
            f"first_nameLIKE{params.query}"
            f"^ORlast_nameLIKE{params.query}"
            f"^ORuser_nameLIKE{params.query}"
            f"^ORemailLIKE{params.query}"
        )
        query_parts.append(f"({search_query})")

    query = "^".join(query_parts) if query_parts else ""

    params_dict = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
    }

    if query:
        params_dict["sysparm_query"] = query

    try:
        response = requests.get(
            api_url,
            params=params_dict,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json()
        users = result.get("result", [])

        formatted_users = []
        for user in users:
            formatted_users.append(
                {
                    "sys_id": user.get("sys_id"),
                    "user_name": user.get("user_name"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "email": user.get("email"),
                    "title": user.get("title"),
                    "department": user.get("department", {}).get("display_value"),
                    "manager": user.get("manager", {}).get("display_value"),
                    "phone": user.get("phone"),
                    "mobile_phone": user.get("mobile_phone"),
                    "location": user.get("location", {}).get("display_value"),
                    "active": user.get("active") == "true",
                }
            )

        return {
            "success": True,
            "message": f"Retrieved {len(formatted_users)} users",
            "users": formatted_users,
            "total": len(formatted_users),
            "limit": params.limit,
            "offset": params.offset,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error listing users: {str(e)}")
        return {"success": False, "message": f"Error listing users: {str(e)}", "users": []}
