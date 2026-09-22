"""Read-only group lookup tools for the ServiceNow MCP server."""

from __future__ import annotations

import logging
from typing import Optional

import requests
from pydantic import BaseModel, Field

from ..auth.auth_manager import AuthManager
from ..utils.config import ServerConfig

logger = logging.getLogger(__name__)


class ListGroupsParams(BaseModel):
    """Parameters for listing ServiceNow assignment groups."""

    limit: int = Field(10, description="Maximum number of groups to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(
        True,
        description="Filter by active status; defaults to active groups only",
    )
    query: Optional[str] = Field(
        None,
        description=(
            "Plain-text term matched with LIKE against the group name. This is "
            "not an encoded ServiceNow query."
        ),
    )


def _display_value(value: object) -> object:
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def list_groups(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListGroupsParams,
) -> dict:
    """List ServiceNow groups so callers can resolve names to sys_ids."""

    api_url = f"{config.api_url}/table/sys_user_group"
    filters = []
    if params.active is not None:
        filters.append(f"active={str(params.active).lower()}")
    if params.query:
        filters.append(f"nameLIKE{params.query}")
    filters.append("ORDERBYname")

    request_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
        "sysparm_fields": "sys_id,name,description,active,manager,parent",
        "sysparm_query": "^".join(filters),
    }

    try:
        response = requests.get(
            api_url,
            params=request_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        groups = []
        for group in response.json().get("result", []):
            groups.append(
                {
                    "sys_id": group.get("sys_id"),
                    "name": group.get("name"),
                    "description": group.get("description"),
                    "active": str(group.get("active", "")).lower() == "true",
                    "manager": _display_value(group.get("manager")),
                    "parent": _display_value(group.get("parent")),
                }
            )

        return {
            "success": True,
            "message": f"Retrieved {len(groups)} groups",
            "groups": groups,
            "returned_count": len(groups),
            "limit": params.limit,
            "offset": params.offset,
            "applied_filters": {
                key: value
                for key, value in {
                    "active": params.active,
                    "query": params.query,
                }.items()
                if value is not None
            },
            "sort": "name_asc",
        }
    except requests.exceptions.RequestException as exc:
        logger.error("Error listing groups: %s", exc)
        return {
            "success": False,
            "message": f"Error listing groups: {exc}",
            "groups": [],
        }
