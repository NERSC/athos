#!/usr/bin/env python3
"""
Iris GraphQL MCP Tool
A FastMCP-based tool for interacting with the Iris GraphQL API
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP instance
mcp = FastMCP("Iris GraphQL API")

class IrisGraphQLClient:
    """Client for interacting with Iris GraphQL API"""
    
    def __init__(self, base_url: str = "https://iris-stage.nersc.gov"):
        self.base_url = base_url
        self.graphql_endpoint = f"{base_url}/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.graphql_endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error executing GraphQL query: {e}")
                raise
            except Exception as e:
                logger.error(f"Error executing GraphQL query: {e}")
                raise

# Initialize GraphQL client
iris_client = IrisGraphQLClient()

@mcp.tool()
async def get_users(uid: Optional[int] = None, year: Optional[int] = None) -> str:
    """
    Retrieve users from the Iris system.
    
    Args:
        uid: Optional user ID to filter by
        year: Optional year to query historical data
    
    Returns:
        JSON string containing user data
    """
    query = """
    query GetUsers($uid: Int, $year: Int) {
        systemInfo {
            users(uid: $uid, year: $year) {
                uid
                email
                name
            }
        }
    }
    """
    
    variables = {}
    if uid is not None:
        variables["uid"] = uid
    if year is not None:
        variables["year"] = year
    
    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving users: {str(e)}"

@mcp.tool()
async def get_user_allocations(uid: Optional[int] = None, year: Optional[int] = None) -> str:
    """
    Get users with their compute allocations per project.
    
    Args:
        uid: Optional user ID to filter by
        year: Optional year to query historical data
    
    Returns:
        JSON string containing user allocation data
    """
    query = """
    query GetUserAllocations($uid: Int, $year: Int) {
        systemInfo {
            users(uid: $uid, year: $year) {
                uid
                email
                name
                userAllocations {
                    userAlloc
                    userAllocPct
                    computeAllocation {
                        currentAlloc
                        project {
                            repoName
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {}
    if uid is not None:
        variables["uid"] = uid
    if year is not None:
        variables["year"] = year
    
    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving user allocations: {str(e)}"

@mcp.tool()
async def get_directories_with_allocations() -> str:
    """
    Download every directory along with allocations, including the user's name.
    
    Returns:
        JSON string containing directory and allocation data
    """
    query = """
    query GetDirectoriesWithAllocations {
        systemInfo {
            fileSystems {
                id
                name
                updatedAt
                directories {
                    path
                    dirType
                    directoryAllocations {
                        user {
                            name
                        }
                        spaceQuota
                    }
                }
            }
        }
    }
    """
    
    try:
        result = await iris_client.execute_query(query)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving directories with allocations: {str(e)}"

@mcp.tool()
async def get_storage_changes(start_date: str, end_date: str) -> str:
    """
    Detect new projects and users by querying storage changes in a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        JSON string containing storage changes
    """
    query = """
    query GetStorageChanges($start: String!, $end: String!) {
        changes {
            storageChanges(start: $start, end: $end) {
                ts
                uid
                gid
                pname
                status
                userName
                store
                inode
                action
            }
        }
    }
    """
    
    variables = {
        "start": start_date,
        "end": end_date
    }
    
    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving storage changes: {str(e)}"

@mcp.tool()
async def get_user_quotas() -> str:
    """
    Get all user quotas (home and scratch).
    
    Returns:
        JSON string containing user quota data
    """
    query = """
    query GetUserQuotas {
        systemInfo {
            userQuotas {
                user {
                    uid
                    name
                }
                homeQuota {
                    store
                    inode
                }
                scratchQuota {
                    store
                    inode
                }
            }
        }
    }
    """
    
    try:
        result = await iris_client.execute_query(query)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving user quotas: {str(e)}"

@mcp.tool()
async def get_project_quotas() -> str:
    """
    Get all project quotas.
    
    Returns:
        JSON string containing project quota data
    """
    query = """
    query GetProjectQuotas {
        systemInfo {
            projectQuotas {
                userId
                groupId
                pname
                status
                quota {
                    store
                    inode
                }
            }
        }
    }
    """
    
    try:
        result = await iris_client.execute_query(query)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving project quotas: {str(e)}"

@mcp.tool()
async def get_storage_archive_user(email: Optional[str] = None, uid: Optional[int] = None) -> str:
    """
    Query storage archive for user information including groups and project roles.
    
    Args:
        email: User email to search for
        uid: User ID to search for
    
    Returns:
        JSON string containing user information from storage archive
    """
    query = """
    query GetStorageArchiveUser($email: String, $uid: Int) {
        storageArchive {
            users(email: $email, uid: $uid) {
                id
                name
                email
                groupUsers {
                    group {
                        name
                        type
                    }
                }
                projectUsers {
                    projectId
                    role
                }
            }
        }
    }
    """
    
    variables = {}
    if email:
        variables["email"] = email
    if uid is not None:
        variables["uid"] = uid
    
    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving storage archive user: {str(e)}"

@mcp.tool()
async def get_storage_archive_group(gid: int) -> str:
    """
    Query storage archive for group information by GID.
    
    Args:
        gid: Group ID to search for
    
    Returns:
        JSON string containing group information
    """
    query = """
    query GetStorageArchiveGroup($gid: Int!) {
        storageArchive {
            groups(gid: $gid) {
                name
                type
            }
        }
    }
    """
    
    variables = {"gid": gid}
    
    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving storage archive group: {str(e)}"

@mcp.tool()
async def get_projdir_users(pname: str) -> str:
    """
    Get users who can access a specific project directory.
    
    Args:
        pname: Project name/directory name
    
    Returns:
        JSON string containing users with access to the project directory
    """
    query = """
    query GetProjdirUsers($pname: String!) {
        storageArchive {
            projdirs(pname: $pname) {
                pname
                project {
                    projectUsers {
                        userId
                        user {
                            name
                            email
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {"pname": pname}
    
    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving projdir users: {str(e)}"

@mcp.tool()
async def get_pending_projdirs() -> str:
    """
    View pending project directory changes that need to be acknowledged.
    
    Returns:
        JSON string containing pending projdir changes
    """
    query = """
    query GetPendingProjdirs {
        pendingProjdirs {
            projdirs {
                pname
                createStatus
                createStatusAt
                oldPname
            }
        }
    }
    """
    
    try:
        result = await iris_client.execute_query(query)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving pending projdirs: {str(e)}"

@mcp.tool()
async def upload_slurm_usage(jobs_data: str) -> str:
    """
    Upload Slurm job usage data to the system.
    
    Args:
        jobs_data: JSON string containing job data array
    
    Returns:
        JSON string with upload status
    """
    try:
        jobs = json.loads(jobs_data)
    except json.JSONDecodeError as e:
        return f"Error parsing jobs data: {str(e)}"
    
    mutation = """
    mutation ComputeUsageMutation($computeUsageInput: ComputeUsageInput!) {
        computeUsage(input: $computeUsageInput) {
            status
            error
        }
    }
    """
    
    variables = {
        "computeUsageInput": {
            "jobs": jobs
        }
    }
    
    try:
        result = await iris_client.execute_query(mutation, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error uploading Slurm usage: {str(e)}"

@mcp.tool()
async def upload_storage_usage(paths_data: str) -> str:
    """
    Upload storage usage data to the system.
    
    Args:
        paths_data: JSON string containing storage usage data array
    
    Returns:
        JSON string with upload status
    """
    try:
        paths = json.loads(paths_data)
    except json.JSONDecodeError as e:
        return f"Error parsing paths data: {str(e)}"
    
    mutation = """
    mutation StorageUsageMutation($storageUsageInput: StorageUsageInput!) {
        storageUsage(input: $storageUsageInput) {
            status
            error
        }
    }
    """
    
    variables = {
        "storageUsageInput": {
            "paths": paths
        }
    }
    
    try:
        result = await iris_client.execute_query(mutation, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error uploading storage usage: {str(e)}"

@mcp.tool()
async def acknowledge_pending_projdirs(pnames: List[str]) -> str:
    """
    Acknowledge pending project directory changes.
    
    Args:
        pnames: List of project names to acknowledge
    
    Returns:
        JSON string with acknowledgment status
    """
    mutation = """
    mutation AckPendingProjdirs($input: AckPendingProjdirsInput!) {
        ackPendingProjdirs(input: $input) {
            status
            error
        }
    }
    """
    
    variables = {
        "input": {
            "pnames": pnames
        }
    }
    
    try:
        result = await iris_client.execute_query(mutation, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error acknowledging pending projdirs: {str(e)}"

@mcp.tool()
async def execute_custom_query(query: str, variables: Optional[str] = None) -> str:
    """
    Execute a custom GraphQL query against the Iris API.
    
    Args:
        query: GraphQL query string
        variables: Optional JSON string of variables
    
    Returns:
        JSON string with query results
    """
    parsed_variables = None
    if variables:
        try:
            parsed_variables = json.loads(variables)
        except json.JSONDecodeError as e:
            return f"Error parsing variables: {str(e)}"
    
    try:
        result = await iris_client.execute_query(query, parsed_variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing custom query: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
