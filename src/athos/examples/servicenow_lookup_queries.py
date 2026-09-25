"""Run a few read-only lookup queries against a live ServiceNow instance.

The example loads ``SERVICENOW_INSTANCE_URL``, ``SERVICENOW_USERNAME``, and
``SERVICENOW_PASSWORD`` from the environment (and, when present, ``.env``).
It exercises the MCP tools end to end without starting a separate server.

Examples:
    python -m athos.examples.servicenow_lookup_queries
    python -m athos.examples.servicenow_lookup_queries \
        --group-query DAS --user-name sfarrell
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from fastmcp import Client

from athos.tools.servicenow_mcp.server import ServiceNowMCPServer
from athos.tools.servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    ServerConfig,
)


def parse_args() -> argparse.Namespace:
    """Parse optional lookup terms for the live queries."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group-query",
        default="DAS",
        help="Group-name search term (default: DAS)",
    )
    parser.add_argument(
        "--user-name",
        default="sfarrell",
        help="Exact ServiceNow username to retrieve (default: sfarrell)",
    )
    return parser.parse_args()


def show(label: str, value: Any) -> None:
    """Print a labeled MCP result in a readable form."""

    print(f"\n=== {label} ===")
    print(json.dumps(value, indent=2, default=str))


async def main() -> None:
    """Run group, group-filtered incident, and user queries."""

    args = parse_args()
    load_dotenv()

    auth = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(
            username=os.environ["SERVICENOW_USERNAME"],
            password=os.environ["SERVICENOW_PASSWORD"],
        ),
    )
    config = ServerConfig(
        instance_url=os.environ["SERVICENOW_INSTANCE_URL"],
        auth=auth,
        read_only=True,
    )

    server = ServiceNowMCPServer(config)
    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "list_groups",
            {"query": args.group_query, "active": True, "limit": 5},
        )
        content = result.structured_content or {}
        show(f'active groups matching "{args.group_query}"', content)

        # Prefer one exact name match when a LIKE search returns related groups
        # such as both "DAS" and "DAS-POC". Otherwise, accept a sole result.
        groups = content.get("groups", [])
        exact_groups = [
            group
            for group in groups
            if str(group.get("name", "")).casefold() == args.group_query.casefold()
        ]
        group = exact_groups[0] if len(exact_groups) == 1 else None
        if group is None and len(groups) == 1:
            group = groups[0]

        if group is not None:
            incidents = await client.call_tool(
                "list_incidents",
                {
                    "assignment_group": group["sys_id"],
                    "active": True,
                    "limit": 3,
                },
            )
            show(
                f'newest active incidents for "{group["name"]}"',
                incidents.structured_content or {},
            )
        else:
            print(
                "\nIncident lookup skipped: the group query did not produce "
                "a unique exact match or a sole result."
            )

        users = await client.call_tool(
            "list_users",
            {"query": args.user_name, "active": True, "limit": 10},
        )
        show(
            f'active users matching "{args.user_name}"',
            users.structured_content or {},
        )

        user = await client.call_tool(
            "get_user",
            {"user_name": args.user_name},
        )
        show(
            f'user with username "{args.user_name}"',
            user.structured_content or {},
        )


if __name__ == "__main__":
    asyncio.run(main())
