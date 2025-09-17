"""ServiceNow MCP server implemented with FastMCP."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Union

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
        if self.config.read_only:
            logger.info(
                "ServiceNow MCP Server running in read-only mode; write tools will be disabled."
            )
        else:
            self._register_write_tools()
        self._register_read_tools()

    def _register_write_tools(self) -> None:
        @self.mcp.tool()
        async def create_incident(
            short_description: str,
            description: Optional[str] = None,
            caller_id: Optional[str] = None,
            category: Optional[str] = None,
            subcategory: Optional[str] = None,
            priority: Optional[str] = None,
            impact: Optional[str] = None,
            urgency: Optional[str] = None,
            assigned_to: Optional[str] = None,
            assignment_group: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Create a new incident in ServiceNow.

            Args:
                short_description: Short description of the incident.
                description: Detailed description of the incident.
                caller_id: User who reported the incident.
                category: Category of the incident.
                subcategory: Subcategory of the incident.
                priority: Priority of the incident.
                impact: Impact of the incident.
                urgency: Urgency of the incident.
                assigned_to: User assigned to the incident.
                assignment_group: Group assigned to the incident.

            Returns:
                Dictionary with the created incident details.
            """
            params = incident_tools.CreateIncidentParams(
                short_description=short_description,
                description=description,
                caller_id=caller_id,
                category=category,
                subcategory=subcategory,
                priority=priority,
                impact=impact,
                urgency=urgency,
                assigned_to=assigned_to,
                assignment_group=assignment_group,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.create_incident, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def update_incident(
            incident_id: str,
            short_description: Optional[str] = None,
            description: Optional[str] = None,
            state: Optional[str] = None,
            category: Optional[str] = None,
            subcategory: Optional[str] = None,
            priority: Optional[str] = None,
            impact: Optional[str] = None,
            urgency: Optional[str] = None,
            assigned_to: Optional[str] = None,
            assignment_group: Optional[str] = None,
            work_notes: Optional[str] = None,
            close_notes: Optional[str] = None,
            close_code: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Update an existing incident in ServiceNow.

            Args:
                incident_id: Incident ID or sys_id.
                short_description: Short description of the incident.
                description: Detailed description of the incident.
                state: State of the incident.
                category: Category of the incident.
                subcategory: Subcategory of the incident.
                priority: Priority of the incident.
                impact: Impact of the incident.
                urgency: Urgency of the incident.
                assigned_to: User assigned to the incident.
                assignment_group: Group assigned to the incident.
                work_notes: Work notes to add to the incident.
                close_notes: Close notes to add to the incident.
                close_code: Close code for the incident.

            Returns:
                Dictionary with the updated incident details.
            """
            params = incident_tools.UpdateIncidentParams(
                incident_id=incident_id,
                short_description=short_description,
                description=description,
                state=state,
                category=category,
                subcategory=subcategory,
                priority=priority,
                impact=impact,
                urgency=urgency,
                assigned_to=assigned_to,
                assignment_group=assignment_group,
                work_notes=work_notes,
                close_notes=close_notes,
                close_code=close_code,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.update_incident, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def add_comment(
            incident_id: str,
            comment: str,
            is_work_note: bool = False,
        ) -> Dict[str, Any]:
            """Add a comment to an incident in ServiceNow.

            Args:
                incident_id: Incident ID or sys_id.
                comment: Comment to add to the incident.
                is_work_note: Whether the comment is a work note.

            Returns:
                Dictionary with the result of the operation.
            """
            params = incident_tools.AddCommentParams(
                incident_id=incident_id,
                comment=comment,
                is_work_note=is_work_note,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.add_comment, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def resolve_incident(
            incident_id: str,
            resolution_code: str,
            resolution_notes: str,
        ) -> Dict[str, Any]:
            """Resolve an incident in ServiceNow.

            Args:
                incident_id: Incident ID or sys_id.
                resolution_code: Resolution code for the incident.
                resolution_notes: Resolution notes for the incident.

            Returns:
                Dictionary with the result of the operation.
            """
            params = incident_tools.ResolveIncidentParams(
                incident_id=incident_id,
                resolution_code=resolution_code,
                resolution_notes=resolution_notes,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.resolve_incident, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

    def _register_read_tools(self) -> None:
        @self.mcp.tool()
        async def list_incidents(
            limit: int = 10,
            offset: int = 0,
            state: Optional[str] = None,
            assigned_to: Optional[str] = None,
            category: Optional[str] = None,
            query: Optional[str] = None,
            incident_number: Optional[str] = None,
        ) -> Dict[str, Any]:
            """List incidents from ServiceNow.

            Args:
                limit: Maximum number of incidents to return.
                offset: Offset for pagination.
                state: Filter by incident state.
                assigned_to: Filter by assigned user.
                category: Filter by category.
                query: Filter by short description or title.
                incident_number: Filter by incident number.

            Returns:
                Dictionary with list of incidents.
            """
            params = incident_tools.ListIncidentsParams(
                limit=limit,
                offset=offset,
                state=state,
                assigned_to=assigned_to,
                category=category,
                query=query,
                incident_number=incident_number,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.list_incidents, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def view_incident_logs(
            limit: int = 10,
            offset: int = 0,
            state: Optional[str] = None,
            assigned_to: Optional[str] = None,
            category: Optional[str] = None,
            query: Optional[str] = None,
            incident_number: Optional[str] = None,
            sys_id: Optional[str] = None,
        ) -> Dict[str, Any]:
            """View the activity logs for an incident in ServiceNow.

            Args:
                limit: Maximum number of incidents to return.
                offset: Offset for pagination.
                state: Filter by incident state.
                assigned_to: Filter by assigned user.
                category: Filter by category.
                query: Filter by short description or title.
                incident_number: Filter by incident number.
                sys_id: Incident sys_id to view logs for directly.

            Returns:
                Dictionary with list of incident logs.
            """
            params = incident_tools.ViewIncidentLogsParams(
                limit=limit,
                offset=offset,
                state=state,
                assigned_to=assigned_to,
                category=category,
                query=query,
                incident_number=incident_number,
                sys_id=sys_id,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.view_incident_logs, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def get_incident_attachments(
            incident_id: str,
            limit: int = 10,
            offset: int = 0,
        ) -> Dict[str, Any]:
            """Get attachments for an incident in ServiceNow."""

            params = incident_tools.GetIncidentAttachmentsParams(
                incident_id=incident_id,
                limit=limit,
                offset=offset,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.get_incident_attachments,
                    self.config,
                    self.auth,
                    params,
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def download_attachment(
            attachment_sys_id: str,
            download_dir: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Download an attachment file from ServiceNow."""

            params = incident_tools.DownloadAttachmentParams(
                attachment_sys_id=attachment_sys_id,
                download_dir=download_dir,
            )
            try:
                return await asyncio.to_thread(
                    incident_tools.download_attachment,
                    self.config,
                    self.auth,
                    params,
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def get_user(
            user_id: Optional[str] = None,
            user_name: Optional[str] = None,
            email: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Get a user from ServiceNow by user ID, username, or email.

            Args:
                user_id: User ID or sys_id.
                user_name: Username of the user.
                email: Email address of the user.

            Returns:
                Dictionary containing user details.
            """
            params = user_tools.GetUserParams(
                user_id=user_id,
                user_name=user_name,
                email=email,
            )
            try:
                return await asyncio.to_thread(
                    user_tools.get_user, self.config, self.auth, params
                )
            except Exception as e:  # pragma: no cover
                return self._handle_error(e)

        @self.mcp.tool()
        async def list_users(
            limit: int = 10,
            offset: int = 0,
            active: Optional[bool] = None,
            department: Optional[str] = None,
            query: Optional[str] = None,
        ) -> Dict[str, Any]:
            """List users from ServiceNow with optional filtering.

            Args:
                limit: Maximum number of users to return.
                offset: Offset for pagination.
                active: Filter by active status.
                department: Filter by department.
                query: Case-insensitive search term matching name, username, or email.

            Returns:
                Dictionary containing list of users.
            """
            params = user_tools.ListUsersParams(
                limit=limit,
                offset=offset,
                active=active,
                department=department,
                query=query,
            )
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


