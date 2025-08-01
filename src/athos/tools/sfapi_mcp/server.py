"""
NERSC SuperFacility API MCP Server

This server provides access to NERSC computing resources through the SuperFacility API.
It supports system status checking, job management, file operations, and command execution.

Authentication is handled via OAuth2 client credentials flow.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NERSCAuth:
    """Handle NERSC SuperFacility API authentication"""
    
    def __init__(self, client_id: str, private_key: str, base_url: str = "https://api.nersc.gov/api/v1.2"):
        self.client_id = client_id
        self.private_key = private_key
        self.base_url = base_url
        self.token_url = "https://oidc.nersc.gov/c2id/token"
        self.access_token = None
        self.token_expires_at = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_access_token(self) -> str:
        """Get or refresh access token"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        # Import authlib here to avoid dependency issues if not installed
        try:
            from authlib.jose import JsonWebSignature
        except ImportError:
            raise ImportError("authlib is required for authentication. Install with: pip install authlib")
        
        try:
            # Create JWT assertion
            now = datetime.now()
            payload = {
                "iss": self.client_id,
                "sub": self.client_id,
                "aud": self.token_url,
                "jti": f"{self.client_id}-{int(now.timestamp())}",
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "iat": int(now.timestamp())
            }
            
            jws = JsonWebSignature()
            client_assertion = jws.serialize_compact(payload, self.private_key, alg="RS256")
            
            # Exchange assertion for access token
            data = {
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": client_assertion
            }
            
            response = await self.client.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Tokens typically expire in 10 minutes, refresh a bit earlier
            self.token_expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 600) - 60)
            
            logger.info("Successfully obtained access token")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to obtain access token: {str(e)}")
            raise
    
    async def request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make authenticated request to NERSC API"""
        try:
            token = await self.get_access_token()
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {token}"
            kwargs["headers"] = headers
            
            url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
            logger.debug(f"Making {method} request to {url}")
            
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make GET request"""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make POST request"""
        return await self.request("POST", endpoint, **kwargs)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class NERSCMCPServer:
    """MCP Server for NERSC SuperFacility API"""
    
    def __init__(self):
        self.mcp = FastMCP("NERSC SuperFacility API")
        self.auth: Optional[NERSCAuth] = None
        self.common_systems = [
            "perlmutter", "cori", "dtn", "archive", "spin", "jupyter"
        ]
        self.setup_tools()
    
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Standardized error handling"""
        error_msg = str(error)
        logger.error(f"Tool error: {error_msg}")
        
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return {
                "error": "Authentication failed. Please check your credentials and try initializing authentication again.",
                "type": "authentication_error"
            }
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            return {
                "error": "Access forbidden. You may need elevated permissions for this operation.",
                "type": "permission_error"
            }
        elif "404" in error_msg or "not found" in error_msg.lower():
            return {
                "error": "Resource not found. Please check the system name and path.",
                "type": "not_found_error"
            }
        elif "timeout" in error_msg.lower():
            return {
                "error": "Request timed out. The system may be experiencing high load.",
                "type": "timeout_error"
            }
        else:
            return {
                "error": error_msg,
                "type": "general_error"
            }
    
    def setup_tools(self):
        """Setup MCP tools"""
        
        @self.mcp.tool()
        async def initialize_auth(
            client_id: str = Field(description="NERSC SuperFacility API client ID"),
            private_key: str = Field(description="Private key for authentication (PEM format)")
        ) -> Dict[str, Any]:
            """Initialize authentication with NERSC SuperFacility API credentials"""
            try:
                self.auth = NERSCAuth(client_id, private_key)
                # Test authentication
                await self.auth.get_access_token()
                logger.info("Authentication initialized successfully")
                return {
                    "status": "success",
                    "message": "Authentication initialized successfully",
                    "client_id": client_id[:8] + "..." if len(client_id) > 8 else client_id
                }
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def get_system_status(
            system: Optional[str] = Field(
                None, 
                description=f"System name (e.g., 'perlmutter', 'cori', 'dtn', 'archive'). If None, returns all systems. Common systems: {', '.join(self.common_systems)}"
            )
        ) -> Dict[str, Any]:
            """Get status of NERSC systems. No authentication required."""
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if system:
                        url = f"https://api.nersc.gov/api/v1.2/status/{system}"
                    else:
                        url = "https://api.nersc.gov/api/v1.2/status"
                    
                    logger.debug(f"Fetching system status from {url}")
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    data = response.json()
                    logger.info(f"Successfully retrieved status for {system or 'all systems'}")
                    return data
                    
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def list_directory(
            system: str = Field(description="System name (e.g., 'perlmutter')"),
            path: str = Field(description="Directory path to list (e.g., '/global/homes/u/username')")
        ) -> Dict[str, Any]:
            """List contents of a directory on a NERSC system. Requires authentication."""
            if not self.auth:
                return {
                    "error": "Authentication not initialized. Call initialize_auth first.",
                    "type": "authentication_required"
                }
            
            try:
                response = await self.auth.get(f"utilities/ls/{system}{path}")
                data = response.json()
                logger.info(f"Successfully listed directory {path} on {system}")
                return data
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def get_file_info(
            system: str = Field(description="System name (e.g., 'perlmutter')"),
            filepath: str = Field(description="Full path to file")
        ) -> Dict[str, Any]:
            """Get information about a specific file on a NERSC system. Requires authentication."""
            if not self.auth:
                return {"error": "Authentication not initialized. Call initialize_auth first."}
            
            try:
                response = await self.auth.get(f"utilities/ls/{system}{filepath}")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def run_command(
            system: str = Field(description="System name (e.g., 'perlmutter')"),
            command: str = Field(description="Command to execute on login node (e.g., 'ls -la', 'cat /path/to/file')")
        ) -> Dict[str, Any]:
            """Execute a command on a NERSC system login node. Requires elevated authentication."""
            if not self.auth:
                return {
                    "error": "Authentication not initialized. Call initialize_auth first.",
                    "type": "authentication_required"
                }
            
            try:
                data = {"executable": command}
                response = await self.auth.post(f"utilities/command/{system}", data=data)
                result = response.json()
                logger.info(f"Successfully submitted command '{command}' on {system}")
                return result
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def submit_job(
            system: str = Field(description="System name (e.g., 'perlmutter')"),
            job_script_path: str = Field(description="Path to job script on the system"),
            is_batch: bool = Field(True, description="True for Slurm batch jobs, False for direct shell execution")
        ) -> Dict[str, Any]:
            """Submit a job to a NERSC system. Requires elevated authentication."""
            if not self.auth:
                return {"error": "Authentication not initialized. Call initialize_auth first."}
            
            try:
                data = {
                    "job": job_script_path,
                    "isPath": is_batch
                }
                response = await self.auth.post(f"compute/jobs/{system}", data=data)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def get_task_status(
            task_id: str = Field(description="Task ID returned from previous API call")
        ) -> Dict[str, Any]:
            """Get status and results of a previously submitted task. Requires authentication."""
            if not self.auth:
                return {
                    "error": "Authentication not initialized. Call initialize_auth first.",
                    "type": "authentication_required"
                }
            
            try:
                response = await self.auth.get(f"tasks/{task_id}")
                data = response.json()
                logger.info(f"Successfully retrieved task status for {task_id}")
                
                # Parse result if it's a JSON string
                if data.get("result") and isinstance(data["result"], str):
                    try:
                        data["parsed_result"] = json.loads(data["result"])
                    except json.JSONDecodeError:
                        pass
                
                return data
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def get_job_queue(
            system: str = Field(description="System name (e.g., 'perlmutter')"),
            user: Optional[str] = Field(None, description="Username to filter jobs (optional)")
        ) -> Dict[str, Any]:
            """Get job queue information for a system. Requires authentication."""
            if not self.auth:
                return {"error": "Authentication not initialized. Call initialize_auth first."}
            
            try:
                endpoint = f"compute/jobs/{system}"
                if user:
                    endpoint += f"?user={user}"
                
                response = await self.auth.get(endpoint)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def get_compute_allocation(
            system: str = Field(description="System name (e.g., 'perlmutter')"),
            repo: Optional[str] = Field(None, description="Repository/project name (optional)")
        ) -> Dict[str, Any]:
            """
            Get compute allocation (i.e. project) information.

            This function requires authentication.
            If the repo argument is not specified, this function will return the
            list of compute allocations from the authenticated user's projects.
            """
            if not self.auth:
                return {"error": "Authentication not initialized. Call initialize_auth first."}
            
            try:
                endpoint = f"account/usage/{system}"
                if repo:
                    endpoint += f"/{repo}"
                
                response = await self.auth.get(endpoint)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def transfer_file(
            source_system: str = Field(description="Source system name"),
            source_path: str = Field(description="Source file path"),
            dest_system: str = Field(description="Destination system name"),
            dest_path: str = Field(description="Destination file path")
        ) -> Dict[str, Any]:
            """Transfer a file between NERSC systems. Requires authentication."""
            if not self.auth:
                return {"error": "Authentication not initialized. Call initialize_auth first."}
            
            try:
                data = {
                    "source_system": source_system,
                    "source_path": source_path,
                    "dest_system": dest_system,
                    "dest_path": dest_path
                }
                response = await self.auth.post("utilities/transfer", data=data)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}
        
        # @self.mcp.tool()
        # async def get_system_info(
        #     system: str = Field(description="System name (e.g., 'perlmutter')")
        # ) -> Dict[str, Any]:
        #     """Get detailed information about a NERSC system. No authentication required."""
        #     try:
        #         async with httpx.AsyncClient() as client:
        #             response = await client.get(f"https://api.nersc.gov/api/v1.2/resources/{system}")
        #             response.raise_for_status()
        #             return response.json()
        #     except Exception as e:
        #         return {"error": str(e)}
        
        @self.mcp.tool()
        async def get_outages(
            system: Optional[str] = Field(None, description="System name (optional)")
        ) -> Dict[str, Any]:
            """Get planned outages and maintenance information. No authentication required."""
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if system:
                        url = f"https://api.nersc.gov/api/v1.2/status/outages/{system}"
                    else:
                        url = "https://api.nersc.gov/api/v1.2/status/outages"
                    
                    logger.debug(f"Fetching outage information from {url}")
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    data = response.json()
                    logger.info(f"Successfully retrieved outage information for {system or 'all systems'}")
                    return data
                    
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def get_available_systems() -> Dict[str, Any]:
            """Get list of available NERSC systems with their current status."""
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get("https://api.nersc.gov/api/v1.2/status")
                    response.raise_for_status()
                    
                    systems = response.json()
                    logger.info("Successfully retrieved all system information")
                    
                    # Format the response for better readability
                    formatted_systems = []
                    for system in systems:
                        formatted_systems.append({
                            "name": system.get("name"),
                            "full_name": system.get("full_name"),
                            "status": system.get("status"),
                            "system_type": system.get("system_type"),
                            "description": system.get("description"),
                            "updated_at": system.get("updated_at")
                        })
                    
                    return {
                        "systems": formatted_systems,
                        "total_count": len(formatted_systems)
                    }
                    
            except Exception as e:
                return self._handle_error(e)
    
    def run(self) -> None:
        """Run the MCP server"""
        logger.info("Starting NERSC SuperFacility API MCP Server")
        try:
            self.mcp.run()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise
        finally:
            logger.info("Shutting down server")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.auth:
            await self.auth.close()
            logger.info("Closed authentication client")

def load_config_from_env() -> Dict[str, str]:
    """Load configuration from environment variables"""
    config = {}
    
    # Check for required environment variables
    client_id = os.getenv("NERSC_CLIENT_ID")
    private_key_path = os.getenv("NERSC_PRIVATE_KEY_PATH")
    
    if client_id:
        config["client_id"] = client_id
    
    if private_key_path and Path(private_key_path).exists():
        config["private_key"] = Path(private_key_path).read_text()
    
    return config

def main():
    """Main entry point"""
    server = NERSCMCPServer()
    
    # Try to auto-initialize authentication from environment
    config = load_config_from_env()
    if config.get("client_id") and config.get("private_key"):
        try:
            # Create auth but don't test it here since we're not in async context
            server.auth = NERSCAuth(config["client_id"], config["private_key"])
            logger.info("Authentication configured from environment variables")
        except Exception as e:
            logger.warning(f"Failed to configure authentication: {str(e)}")
    
    try:
        server.run()
    finally:
        # Run cleanup in async context if needed
        if server.auth:
            try:
                asyncio.run(server.cleanup())
            except Exception as e:
                logger.warning(f"Error during cleanup: {str(e)}")


def cli() -> None:
    """Entry point for the ``nersc-sfapi-mcp`` console script."""
    main()

if __name__ == "__main__":
    cli()
