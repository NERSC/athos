"""
ServiceNow MCP Server

A Model Context Protocol (MCP) server implementation for ServiceNow,
focusing on the ITSM module.
"""

__version__ = "0.1.0"

from .server import ServiceNowMCPServer

__all__ = ["ServiceNowMCPServer"]
