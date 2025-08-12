"""ServiceNow MCP server implemented with FastMCP."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Union

from fastmcp import FastMCP

from .auth.auth_manager import AuthManager
from .utils.config import ServerConfig
from .tools import incident_tools, user_tools

logger = logging.getLogger(__name__)


class ServiceNowMCPServer:
    """FastMCP based ServiceNow server."""

    def __init__(self, config: Union[ServerConfig, Dict[str, Any]]):
        if isinstance(config, dict):
            self.config = ServerConfig(**config)
        else:
            self.config = config

        self.auth = AuthManager(self.config.auth)
        self.mcp = FastMCP("ServiceNow")
        self._setup_tools()

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        logger.error("Tool error: %s", error)
        return {"error": str(error)}

    def _setup_tools(self) -> None:
        @self.mcp.tool()
        async def create_incident(
            params: incident_tools.CreateIncidentParams,
        ) -> Dict[str, Any]:
            """Create a ServiceNow incident."""
            try:
                return await asyncio.to_thread(
                    incident_tools.create_incident, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def update_incident(
            params: incident_tools.UpdateIncidentParams,
        ) -> Dict[str, Any]:
            """Update a ServiceNow incident."""
            try:
                return await asyncio.to_thread(
                    incident_tools.update_incident, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def add_comment(
            params: incident_tools.AddCommentParams,
        ) -> Dict[str, Any]:
            """Add a comment or work note to an incident."""
            try:
                return await asyncio.to_thread(
                    incident_tools.add_comment, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def resolve_incident(
            params: incident_tools.ResolveIncidentParams,
        ) -> Dict[str, Any]:
            """Resolve an incident with notes."""
            try:
                return await asyncio.to_thread(
                    incident_tools.resolve_incident, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def list_incidents(
            params: incident_tools.ListIncidentsParams,
        ) -> Dict[str, Any]:
            """List recent incidents."""
            try:
                return await asyncio.to_thread(
                    incident_tools.list_incidents, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def view_incident_logs(
            params: incident_tools.ViewIncidentLogsParams,
        ) -> Dict[str, Any]:
            """View activity logs for an incident."""
            try:
                return await asyncio.to_thread(
                    incident_tools.view_incident_logs, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def get_user(
            params: user_tools.GetUserParams,
        ) -> Dict[str, Any]:
            """Retrieve a user record."""
            try:
                return await asyncio.to_thread(
                    user_tools.get_user, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def list_users(
            params: user_tools.ListUsersParams,
        ) -> Dict[str, Any]:
            """List users from ServiceNow."""
            try:
                return await asyncio.to_thread(
                    user_tools.list_users, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

    def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting ServiceNow MCP Server")
        self.mcp.run()


