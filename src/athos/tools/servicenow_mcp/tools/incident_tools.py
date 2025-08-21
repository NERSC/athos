"""
Incident tools for the ServiceNow MCP server.

This module provides tools for managing incidents in ServiceNow.
"""

import logging
from typing import Optional
from pathlib import Path
from email.message import Message
from email.utils import collapse_rfc2231_value

import requests
from pydantic import BaseModel, Field

from ..auth.auth_manager import AuthManager
from ..utils.config import ServerConfig

logger = logging.getLogger(__name__)


def filename_from_content_disposition(cd_header: str, fallback: str) -> str:
    """Parse Content-Disposition to extract a safe filename."""
    if not cd_header:
        return Path(fallback).name

    msg = Message()
    msg["Content-Disposition"] = cd_header

    param = msg.get_param("filename", header="content-disposition")
    if not param:
        param = msg.get_param("filename*", header="content-disposition")

    name = collapse_rfc2231_value(param) if param else fallback
    return Path(name).name


class CreateIncidentParams(BaseModel):
    """Parameters for creating an incident."""

    short_description: str = Field(..., description="Short description of the incident")
    description: Optional[str] = Field(None, description="Detailed description of the incident")
    caller_id: Optional[str] = Field(None, description="User who reported the incident")
    category: Optional[str] = Field(None, description="Category of the incident")
    subcategory: Optional[str] = Field(None, description="Subcategory of the incident")
    priority: Optional[str] = Field(None, description="Priority of the incident")
    impact: Optional[str] = Field(None, description="Impact of the incident")
    urgency: Optional[str] = Field(None, description="Urgency of the incident")
    assigned_to: Optional[str] = Field(None, description="User assigned to the incident")
    assignment_group: Optional[str] = Field(None, description="Group assigned to the incident")


class UpdateIncidentParams(BaseModel):
    """Parameters for updating an incident."""

    incident_id: str = Field(..., description="Incident ID or sys_id")
    short_description: Optional[str] = Field(None, description="Short description of the incident")
    description: Optional[str] = Field(None, description="Detailed description of the incident")
    state: Optional[str] = Field(None, description="State of the incident")
    category: Optional[str] = Field(None, description="Category of the incident")
    subcategory: Optional[str] = Field(None, description="Subcategory of the incident")
    priority: Optional[str] = Field(None, description="Priority of the incident")
    impact: Optional[str] = Field(None, description="Impact of the incident")
    urgency: Optional[str] = Field(None, description="Urgency of the incident")
    assigned_to: Optional[str] = Field(None, description="User assigned to the incident")
    assignment_group: Optional[str] = Field(None, description="Group assigned to the incident")
    work_notes: Optional[str] = Field(None, description="Work notes to add to the incident")
    close_notes: Optional[str] = Field(None, description="Close notes to add to the incident")
    close_code: Optional[str] = Field(None, description="Close code for the incident")


class AddCommentParams(BaseModel):
    """Parameters for adding a comment to an incident."""

    incident_id: str = Field(..., description="Incident ID or sys_id")
    comment: str = Field(..., description="Comment to add to the incident")
    is_work_note: bool = Field(False, description="Whether the comment is a work note")


class ResolveIncidentParams(BaseModel):
    """Parameters for resolving an incident."""

    incident_id: str = Field(..., description="Incident ID or sys_id")
    resolution_code: str = Field(..., description="Resolution code for the incident")
    resolution_notes: str = Field(..., description="Resolution notes for the incident")


class ListIncidentsParams(BaseModel):
    """Parameters for listing incidents."""
    
    limit: int = Field(10, description="Maximum number of incidents to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by incident state")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned user")
    category: Optional[str] = Field(None, description="Filter by category")
    query: Optional[str] = Field(None, description="Filter by short description or title")
    incident_number: Optional[str] = Field(None, description="Filter by incident number")


class IncidentResponse(BaseModel):
    """Response from incident operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    incident_id: Optional[str] = Field(None, description="ID of the affected incident")
    incident_number: Optional[str] = Field(None, description="Number of the affected incident")


class ViewIncidentLogsParams(BaseModel):
    """Parameters for viewing the activity logs for an incident."""

    limit: int = Field(10, description="Maximum number of incidents to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by incident state")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned user")
    category: Optional[str] = Field(None, description="Filter by category")
    query: Optional[str] = Field(None, description="Filter by short description or title")
    incident_number: Optional[str] = Field(None, description="Filter by incident number")
    sys_id: Optional[str] = Field(None, description="Filter by sys_id")


def view_incident_logs(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ViewIncidentLogsParams,
) -> dict:
    """
    View the activity logs for an incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for viewing incident logs.

    Returns:
        Dictionary with list of incident logs.
    """
    # First determine the sys_id to use
    sys_id = params.sys_id
    
    # If no sys_id provided, try to find the incident first
    if not sys_id:
        list_params = ListIncidentsParams(
            limit=1,
            offset=0,
            state=params.state,
            assigned_to=params.assigned_to,
            category=params.category,
            query=params.query,
            incident_number=params.incident_number
        )
        
        incidents_result = list_incidents(config, auth_manager, list_params)
        if not incidents_result["success"] or not incidents_result["incidents"]:
            return {
                "success": False,
                "message": "No matching incident found",
                "logs": []
            }
        
        sys_id = incidents_result["incidents"][0]["sys_id"]

    # Now query the journal entries
    api_url = f"{config.api_url}/table/sys_journal_field"
    
    # Build query parameters
    query_params = {
        "sysparm_query": f"element_id={sys_id}^name=incident",
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true"
    }
    
    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        data = response.json()
        logs = []
        
        for log_entry in data.get("result", []):
            log = {
                "sys_id": log_entry.get("sys_id"),
                "value": log_entry.get("value"),
                "element_id": log_entry.get("element_id"),
                "name": log_entry.get("name"),
                "created_on": log_entry.get("sys_created_on"),
                "created_by": log_entry.get("sys_created_by"),
                "element": log_entry.get("element"),
                "sys_tags": log_entry.get("sys_tags")
            }
            logs.append(log)
        
        return {
            "success": True,
            "message": f"Found {len(logs)} log entries",
            "logs": logs
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch incident logs: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch incident logs: {str(e)}",
            "logs": []
        }


class GetIncidentAttachmentsParams(BaseModel):
    """Parameters for retrieving attachments for an incident."""

    incident_id: str = Field(..., description="Incident ID or sys_id")
    limit: int = Field(10, description="Maximum number of attachments to return")
    offset: int = Field(0, description="Offset for pagination")


class DownloadAttachmentParams(BaseModel):
    """Parameters for downloading an attachment file."""

    attachment_sys_id: str = Field(..., description="Sys ID of the attachment")
    download_dir: str = Field(..., description="Directory to save the file")


def get_incident_attachments(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetIncidentAttachmentsParams,
) -> dict:
    """Retrieve attachments for an incident in ServiceNow."""

    incident_id = params.incident_id

    # Determine sys_id from incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        sys_id = incident_id
    else:
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return {
                    "success": False,
                    "message": f"Incident not found: {incident_id}",
                    "attachments": [],
                }

            sys_id = result[0].get("sys_id")

        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return {
                "success": False,
                "message": f"Failed to find incident: {str(e)}",
                "attachments": [],
            }

    api_url = f"{config.api_url}/attachment"
    query_params = {
        "table_name": "incident",
        "table_sys_id": sys_id,
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
    }

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        attachments = []

        for att_data in data.get("result", []):
            attachment = {
                "sys_id": att_data.get("sys_id"),
                "file_name": att_data.get("file_name"),
                "content_type": att_data.get("content_type"),
                "size_bytes": att_data.get("size_bytes"),
                "download_link": att_data.get("download_link"),
            }
            attachments.append(attachment)

        return {
            "success": True,
            "message": f"Found {len(attachments)} attachments",
            "attachments": attachments,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to fetch incident attachments: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch incident attachments: {str(e)}",
            "attachments": [],
        }


def download_attachment(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DownloadAttachmentParams,
) -> dict:
    """Download an attachment file from ServiceNow."""

    api_url = f"{config.api_url}/attachment/{params.attachment_sys_id}/file"

    try:
        with requests.get(
            api_url,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
            stream=True,
        ) as response:
            response.raise_for_status()

            content_disposition = response.headers.get("Content-Disposition", "")
            filename = filename_from_content_disposition(
                content_disposition, params.attachment_sys_id
            )

            download_path = Path(params.download_dir)
            download_path.mkdir(parents=True, exist_ok=True)
            file_path = download_path / filename

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return {
            "success": True,
            "message": "Attachment downloaded",
            "file_path": str(file_path),
        }

    except requests.RequestException as e:
        logger.error(f"Failed to download attachment: {e}")
        return {
            "success": False,
            "message": f"Failed to download attachment: {str(e)}",
            "file_path": None,
        }


def create_incident(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateIncidentParams,
) -> dict:
    """
    Create a new incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating the incident.

    Returns:
        Dictionary with the created incident details.
    """
    api_url = f"{config.api_url}/table/incident"

    # Build request data
    data = {
        "short_description": params.short_description,
    }

    if params.description:
        data["description"] = params.description
    if params.caller_id:
        data["caller_id"] = params.caller_id
    if params.category:
        data["category"] = params.category
    if params.subcategory:
        data["subcategory"] = params.subcategory
    if params.priority:
        data["priority"] = params.priority
    if params.impact:
        data["impact"] = params.impact
    if params.urgency:
        data["urgency"] = params.urgency
    if params.assigned_to:
        data["assigned_to"] = params.assigned_to
    if params.assignment_group:
        data["assignment_group"] = params.assignment_group

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return {
            "success": True,
            "message": "Incident created successfully",
            "incident_id": result.get("sys_id"),
            "incident_number": result.get("number"),
        }

    except requests.RequestException as e:
        logger.error(f"Failed to create incident: {e}")
        return {
            "success": False,
            "message": f"Failed to create incident: {str(e)}",
        }


def update_incident(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateIncidentParams,
) -> dict:
    """
    Update an existing incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for updating the incident.

    Returns:
        Dictionary with the updated incident details.
    """
    # Determine if incident_id is a number or sys_id
    incident_id = params.incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        # This is likely a sys_id
        api_url = f"{config.api_url}/table/incident/{incident_id}"
    else:
        # This is likely an incident number
        # First, we need to get the sys_id
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return {
                    "success": False,
                    "message": f"Incident not found: {incident_id}",
                }

            incident_id = result[0].get("sys_id")
            api_url = f"{config.api_url}/table/incident/{incident_id}"

        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return {
                "success": False,
                "message": f"Failed to find incident: {str(e)}",
            }

    # Build request data
    data = {}

    if params.short_description:
        data["short_description"] = params.short_description
    if params.description:
        data["description"] = params.description
    if params.state:
        data["state"] = params.state
    if params.category:
        data["category"] = params.category
    if params.subcategory:
        data["subcategory"] = params.subcategory
    if params.priority:
        data["priority"] = params.priority
    if params.impact:
        data["impact"] = params.impact
    if params.urgency:
        data["urgency"] = params.urgency
    if params.assigned_to:
        data["assigned_to"] = params.assigned_to
    if params.assignment_group:
        data["assignment_group"] = params.assignment_group
    if params.work_notes:
        data["work_notes"] = params.work_notes
    if params.close_notes:
        data["close_notes"] = params.close_notes
    if params.close_code:
        data["close_code"] = params.close_code

    # Make request
    try:
        response = requests.put(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return {
            "success": True,
            "message": "Incident updated successfully",
            "incident_id": result.get("sys_id"),
            "incident_number": result.get("number"),
        }

    except requests.RequestException as e:
        logger.error(f"Failed to update incident: {e}")
        return {
            "success": False,
            "message": f"Failed to update incident: {str(e)}",
        }


def add_comment(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: AddCommentParams,
) -> dict:
    """
    Add a comment to an incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for adding the comment.

    Returns:
        Dictionary with the result of the operation.
    """
    # Determine if incident_id is a number or sys_id
    incident_id = params.incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        # This is likely a sys_id
        api_url = f"{config.api_url}/table/incident/{incident_id}"
    else:
        # This is likely an incident number
        # First, we need to get the sys_id
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return {
                    "success": False,
                    "message": f"Incident not found: {incident_id}",
                }

            incident_id = result[0].get("sys_id")
            api_url = f"{config.api_url}/table/incident/{incident_id}"

        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return {
                "success": False,
                "message": f"Failed to find incident: {str(e)}",
            }

    # Build request data
    data = {}

    if params.is_work_note:
        data["work_notes"] = params.comment
    else:
        data["comments"] = params.comment

    # Make request
    try:
        response = requests.put(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return {
            "success": True,
            "message": "Comment added successfully",
            "incident_id": result.get("sys_id"),
            "incident_number": result.get("number"),
        }

    except requests.RequestException as e:
        logger.error(f"Failed to add comment: {e}")
        return {
            "success": False,
            "message": f"Failed to add comment: {str(e)}",
        }


def resolve_incident(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ResolveIncidentParams,
) -> dict:
    """
    Resolve an incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for resolving the incident.

    Returns:
        Dictionary with the result of the operation.
    """
    # Determine if incident_id is a number or sys_id
    incident_id = params.incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        # This is likely a sys_id
        api_url = f"{config.api_url}/table/incident/{incident_id}"
    else:
        # This is likely an incident number
        # First, we need to get the sys_id
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return {
                    "success": False,
                    "message": f"Incident not found: {incident_id}",
                }

            incident_id = result[0].get("sys_id")
            api_url = f"{config.api_url}/table/incident/{incident_id}"

        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return {
                "success": False,
                "message": f"Failed to find incident: {str(e)}",
            }

    # Build request data
    data = {
        "state": "6",  # Resolved
        "close_code": params.resolution_code,
        "close_notes": params.resolution_notes,
        "resolved_at": "now",
    }

    # Make request
    try:
        response = requests.put(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return {
            "success": True,
            "message": "Incident resolved successfully",
            "incident_id": result.get("sys_id"),
            "incident_number": result.get("number"),
        }

    except requests.RequestException as e:
        logger.error(f"Failed to resolve incident: {e}")
        return {
            "success": False,
            "message": f"Failed to resolve incident: {str(e)}",
        }


def list_incidents(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListIncidentsParams,
) -> dict:
    """
    List incidents from ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing incidents.

    Returns:
        Dictionary with list of incidents.
    """
    api_url = f"{config.api_url}/table/incident"

    # Build query parameters
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }
    
    # Add filters
    filters = []
    if params.state:
        filters.append(f"state={params.state}")
    if params.assigned_to:
        filters.append(f"assigned_to={params.assigned_to}")
    if params.category:
        filters.append(f"category={params.category}")
    if params.query:
        filters.append(f"short_descriptionLIKE{params.query}^ORdescriptionLIKE{params.query}")
    if params.incident_number:
        filters.append(f"number={params.incident_number}")
    
    if filters:
        query_params["sysparm_query"] = "^".join(filters)
    
    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        data = response.json()
        incidents = []
        
        for incident_data in data.get("result", []):
            # Handle assigned_to field which could be a string or a dictionary
            assigned_to = incident_data.get("assigned_to")
            if isinstance(assigned_to, dict):
                assigned_to = assigned_to.get("display_value")

            # Handle assignment_group field which could be a string or a dictionary
            assignment_group = incident_data.get("assignment_group")
            if isinstance(assignment_group, dict):
                assignment_group = assignment_group.get("display_value")

            incident = {
                "sys_id": incident_data.get("sys_id"),
                "number": incident_data.get("number"),
                "short_description": incident_data.get("short_description"),
                "description": incident_data.get("description"),
                "state": incident_data.get("state"),
                "priority": incident_data.get("priority"),
                "assigned_to": assigned_to,
                "assignment_group": assignment_group,
                "category": incident_data.get("category"),
                "subcategory": incident_data.get("subcategory"),
                "created_on": incident_data.get("sys_created_on"),
                "updated_on": incident_data.get("sys_updated_on"),
            }
            incidents.append(incident)
        
        return {
            "success": True,
            "message": f"Found {len(incidents)} incidents",
            "incidents": incidents
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to list incidents: {e}")
        return {
            "success": False,
            "message": f"Failed to list incidents: {str(e)}",
            "incidents": []
        }

