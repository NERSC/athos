"""Run a few read-only lookup queries against a live ServiceNow instance.

The example loads ``SERVICENOW_INSTANCE_URL``, ``SERVICENOW_USERNAME``, and
``SERVICENOW_PASSWORD`` from the environment (and, when present, ``.env``).
It exercises the MCP tools end to end without starting a separate server.

Examples:
    python -m athos.examples.servicenow_lookup_queries
    python -m athos.examples.servicenow_lookup_queries \
        --group-query DAS --group-query Storage --user-query alice
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
        action="append",
        dest="group_queries",
        help=(
            "Group-name search term; repeat for multiple queries "
            "(default: DAS, Storage)"
        ),
    )
    parser.add_argument(
        "--user-query",
        default="admin",
        help="User name, username, or email search term (default: admin)",
    )
    return parser.parse_args()


def show(label: str, value: Any) -> None:
    """Print a labeled MCP result in a readable form."""

    print(f"\n=== {label} ===")
    print(json.dumps(value, indent=2, default=str))


async def main() -> None:
    """Run group, group-filtered incident, and user queries."""

    args = parse_args()
    group_queries = args.group_queries or ["DAS", "Storage"]
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
        for index, query in enumerate(group_queries):
            result = await client.call_tool(
                "list_groups",
                {"query": query, "active": True, "limit": 5},
            )
            content = result.structured_content or {}
            show(f'active groups matching "{query}"', content)

            # Demonstrate the intended name -> sys_id -> incident lookup flow for
            # the first query, but do not guess when the name is ambiguous.
            groups = content.get("groups", [])
            if index == 0 and len(groups) == 1:
                group = groups[0]
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
            elif index == 0:
                print(
                    "\nIncident lookup skipped: refine the first group query "
                    "until it returns exactly one group."
                )

        users = await client.call_tool(
            "list_users",
            {"query": args.user_query, "active": True, "limit": 5},
        )
        show(
            f'active users matching "{args.user_query}"',
            users.structured_content or {},
        )


if __name__ == "__main__":
    asyncio.run(main())
