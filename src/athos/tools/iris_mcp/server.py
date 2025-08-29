#!/usr/bin/env python3
"""
Iris GraphQL MCP Tool
A FastMCP-based tool for interacting with the Iris GraphQL API.

This module exposes a FastMCP server with a collection of tools that talk to
the Iris GraphQL API.  The code was originally imported from another project
and has been adapted for use within ATHOS.  To match the behaviour of the other
MCP servers in this repository, a small command line interface is provided at
the end of the module.
"""

import argparse
import json
import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP instance
mcp = FastMCP("Iris GraphQL API")

class IrisGraphQLClient:
    """Client for interacting with Iris GraphQL API"""
    
    def __init__(self, base_url: str = "https://iris.nersc.gov"):
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
async def get_project_info(pname: str) -> str:
    """Retrieve detailed information about a project."""

    query = """
    query GetProjectInfo($pname: String!) {
        systemInfo {
            projects(repoName: $pname, first: 1) {
                code
                description
                repoName
                projectGoals
                program { name }
                organization { code }
                computeAllocations {
                    repoName
                    currentAlloc
                    usedAlloc
                    initialAlloc
                }
                projectQuotas {
                    userId
                    groupId
                    projectId
                    pname
                    # status
                    quota {
                        store
                        inode
                    }
                }
                projdirs {
                    pname
                    fileSystemName
                    fileCount
                    bytesUsed
                }
                projectUsers {
                    user {
                        name
                    }
                    simRole {
                        name
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
        return f"Error retrieving project info: {str(e)}"


@mcp.tool()
async def get_user_info(
    username: Optional[str] = None, uid: Optional[int] = None
) -> str:
    """Retrieve detailed information about a user."""

    if username is None and uid is None:
        return "Error: either username or uid must be provided"

    query = """
    query GetUserInfo($username: String, $uid: Int) {
        systemInfo {
            users(name: $username, uid: $uid) {
                id
                name
                email
                uid
                projects {
                    repoName
                    code
                }
                groups {
                    name
                }
            }
        }
    }
    """

    variables = {}
    if username is not None:
        variables["username"] = username
    if uid is not None:
        variables["uid"] = uid

    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving user info: {str(e)}"


@mcp.tool()
async def get_compute_allocations(
    repo_name: Optional[str] = None,
    year: Optional[int] = None
) -> str:
    """Retrieve compute allocation information.

    Args:
    - repo_name: name of the allocation, e.g. m1234_g project m1234's gpu allocation.
    - year: leave as None for current year.
    """

    query = """
    query GetComputeAllocations($repoName: String, $year: Int) {
        systemInfo {
            computeAllocations(repoName: $repoName, year: $year) {
                repoName
                initialRequest
                finalAward
                initialAlloc
                currentAlloc
                usedAlloc
            }
        }
    }
    """

    variables = {}
    if repo_name is not None:
        variables["repoName"] = repo_name
    if year is not None:
        variables["year"] = year

    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving compute allocations: {str(e)}"


@mcp.tool()
async def get_user_quotas(
    uid: Optional[int] = None, year: Optional[int] = None
) -> str:
    """Retrieve quota information for users."""

    query = """
    query GetUserQuotas($uid: Int, $year: Int) {
        systemInfo {
            userQuotas(uid: $uid, year: $year) {
                id
                user {
                    name
                    uid
                    email
                }
                homeQuota {
                    id
                    type
                    store
                    inode
                    end
                }
                scratchQuota {
                    id
                    type
                    store
                    inode
                    end
                }
                createdAt
                updatedAt
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
        return f"Error retrieving user quotas: {str(e)}"


@mcp.tool()
async def get_project_quotas(
    repo_name: Optional[str] = None, year: Optional[int] = None
) -> str:
    """Retrieve quota information for projects."""

    query = """
    query GetProjectQuotas($repoName: String, $year: Int) {
        systemInfo {
            projectQuotas(repoName: $repoName, year: $year) {
                id
                pname
                status
                project {
                    code
                    label
                }
                user {
                    name
                }
                quota {
                    type
                    store
                    inode
                    end
                }
                paidQuota {
                    type
                    store
                    inode
                    end
                }
                tmpQuota {
                    type
                    store
                    inode
                    end
                }
                createdAt
                updatedAt
            }
        }
    }
    """

    variables = {}
    if repo_name is not None:
        variables["repoName"] = repo_name
    if year is not None:
        variables["year"] = year

    try:
        result = await iris_client.execute_query(query, variables)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving project quotas: {str(e)}"

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


def load_config(base_url_arg: Optional[str] = None) -> Dict[str, str]:
    """Load server configuration from arguments or environment variables."""

    base_url = base_url_arg or os.getenv("IRIS_BASE_URL") or "https://iris.nersc.gov"
    return {"base_url": base_url}


def run_server(base_url: str) -> None:
    """Configure the client and start the MCP server."""

    global iris_client
    iris_client = IrisGraphQLClient(base_url)
    mcp.run()


def main() -> None:
    """Main entry point for the ``iris-mcp`` console script."""

    parser = argparse.ArgumentParser(description="Iris GraphQL MCP server")
    parser.add_argument("--base-url", help="Base URL for the Iris service", default=None)
    args = parser.parse_args()

    config = load_config(args.base_url)
    run_server(config["base_url"])


def cli() -> None:
    """Console script entry point."""
    main()


if __name__ == "__main__":
    cli()
