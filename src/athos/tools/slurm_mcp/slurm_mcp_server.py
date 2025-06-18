#!/usr/bin/env python3
"""
MCP Server for SLURM command execution.

This server provides tools for executing common SLURM commands with safety checks.
Supported commands:
- sacct: Account information for jobs
- showquota: Display quota information
- sinfo: Information about SLURM nodes and partitions
"""

import asyncio
import subprocess
from typing import Any, List, Optional
import argparse
import logging
import re

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slurm-mcp-server")

# Create the server instance
server = Server("slurm-mcp-server")

# Security configuration
DANGEROUS_CHARS = [';', '&', '|', '`', '$', '>', '<', '(', ')', '{', '}', '[', ']']
ALLOWED_COMMANDS = ['sacct', 'showquota', 'sinfo']

class SlurmCommandExecutor:
    """Handles secure execution of SLURM commands."""
    
    @staticmethod
    def validate_arguments(args: List[str], command: str) -> None:
        """
        Validate command arguments for security.
        
        Args:
            args: List of arguments to validate
            command: The SLURM command being executed
            
        Raises:
            ValueError: If arguments contain dangerous content
        """
        # Check for dangerous characters
        for arg in args:
            if any(c in str(arg) for c in DANGEROUS_CHARS):
                raise ValueError(f"Invalid character in argument: {arg}")
        
        # Command-specific validation
        if command == 'sacct':
            SlurmCommandExecutor._validate_sacct_args(args)
        elif command == 'showquota':
            SlurmCommandExecutor._validate_showquota_args(args)
        elif command == 'sinfo':
            SlurmCommandExecutor._validate_sinfo_args(args)
    
    @staticmethod
    def _validate_sacct_args(args: List[str]) -> None:
        """Validate sacct command arguments."""
        for arg in args:
            arg_str = str(arg).strip()
            if arg_str.startswith('-') and len(arg_str) > 1:
                # Allow valid sacct options
                continue
            elif arg_str and not arg_str.replace('-', '').replace('_', '').replace('.', '').replace('/', '').replace(':', '').isalnum():
                if not all(c.isalnum() or c in '-_./: ' for c in arg_str):
                    raise ValueError(f"Potentially unsafe argument: {arg}")
    
    @staticmethod
    def _validate_showquota_args(args: List[str]) -> None:
        """Validate showquota command arguments."""
        # showquota typically doesn't take any parameters
        if args:
            raise ValueError("showquota command does not accept any parameters")
    
    @staticmethod
    def _validate_sinfo_args(args: List[str]) -> None:
        """Validate sinfo command arguments."""
        for arg in args:
            arg_str = str(arg).strip()
            if arg_str.startswith('-') and len(arg_str) > 1:
                # Allow valid sinfo options
                continue
            elif arg_str and not arg_str.replace('-', '').replace('_', '').replace('.', '').replace('/', '').replace(':', '').isalnum():
                if not all(c.isalnum() or c in '-_./: ' for c in arg_str):
                    raise ValueError(f"Potentially unsafe argument: {arg}")
    
    @staticmethod
    async def execute_command(command: str, args: List[str]) -> str:
        """
        Execute a SLURM command with the given arguments.
        
        Args:
            command: The SLURM command to execute
            args: List of arguments to pass to the command
            
        Returns:
            The output of the command as a string
            
        Raises:
            ValueError: If the command contains invalid characters
            RuntimeError: If the command execution fails
        """
        # Validate command
        if command not in ALLOWED_COMMANDS:
            raise ValueError(f"Command not allowed: {command}")
        
        # Validate arguments
        SlurmCommandExecutor.validate_arguments(args, command)
        
        # Construct the full command
        full_command = [command] + args
        
        logger.debug(f"Executing command: {' '.join(full_command)}")
        
        try:
            # Execute the command asynchronously
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=None  # Use current environment
            )
            
            stdout, stderr = await process.communicate()
            
            # Decode the output
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""
            
            logger.debug(f"Command return code: {process.returncode}")
            logger.debug(f"stdout length: {len(stdout_text)}")
            logger.debug(f"stderr length: {len(stderr_text)}")
            
            if process.returncode == 0:
                return stdout_text if stdout_text else f"{command} executed successfully (no output)"
            else:
                error_msg = f"{command} failed with return code {process.returncode}"
                if stderr_text:
                    error_msg += f": {stderr_text}"
                raise RuntimeError(error_msg)
                
        except FileNotFoundError:
            raise RuntimeError(f"{command} command not found. Make sure SLURM is installed and in PATH.")
        except Exception as e:
            logger.error(f"Exception during command execution: {type(e).__name__}: {str(e)}")
            raise RuntimeError(f"Failed to execute {command} command: {str(e)}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema.
    """
    return [
        Tool(
            name="sacct",
            description="Execute SLURM sacct command to get account information for jobs",
            inputSchema={
                "type": "object",
                "properties": {
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments to pass to the sacct command (e.g., ['-S', 'today', '--format=JobID,JobName,State'])",
                        "default": []
                    }
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="showquota",
            description="Execute SLURM showquota command to display quota information for the current user (no parameters needed)",
            inputSchema={
                "type": "object",
                "properties": {
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments to pass to the showquota command (should be empty array as showquota takes no parameters)",
                        "default": []
                    }
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="sinfo",
            description="Execute SLURM sinfo command to get information about nodes and partitions",
            inputSchema={
                "type": "object",
                "properties": {
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments to pass to the sinfo command (e.g., ['-N', '--format=NodeList,State,CPUs'])",
                        "default": []
                    }
                },
                "additionalProperties": False,
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """
    Handle tool execution requests.
    """
    if name not in ALLOWED_COMMANDS:
        raise ValueError(f"Unknown tool: {name}")
    
    # Extract arguments
    args = arguments.get("args", [])
    
    # Validate arguments type
    if not isinstance(args, list):
        raise ValueError("Arguments must be a list of strings")
    
    # Ensure all arguments are strings
    args = [str(arg) for arg in args]
    
    try:
        result = await SlurmCommandExecutor.execute_command(name, args)
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        error_msg = f"Error executing {name} command: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="SLURM MCP Server")
    parser.add_argument("--log-level", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO",
                       help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info("Starting SLURM MCP Server")
    logger.info(f"Available commands: {', '.join(ALLOWED_COMMANDS)}")
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="slurm-mcp-server",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 