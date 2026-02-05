"""Base class for LangGraph flows with common functionality."""

from __future__ import annotations

import logging
from typing import Optional

from athos.config.models import AthosConfig, ModelConfig, ToolConfig, MCPServerConfig
from athos.interfaces.base_flow import BaseFlow

logger = logging.getLogger(__name__)


class BaseLangGraphFlow(BaseFlow):
    """Base class for LangGraph flows providing common functionality.

    This base class provides utilities for accessing ATHOS configuration
    without imposing specific architectural requirements (e.g., single model,
    specific tools, etc.). Subclasses can use these helpers as needed.

    Subclasses should:
    - Set class-level metadata: name, description, supported_modes
    - Implement execute(FlowInput) -> FlowOutput
    - Optionally override initialize() for custom setup
    - Optionally override cleanup() for resource cleanup
    """

    def __init__(self, full_config: Optional[AthosConfig] = None) -> None:
        """Initialize with optional full ATHOS configuration.

        Args:
            full_config: Complete ATHOS configuration for accessing models, tools, etc.
        """
        self._full_config = full_config

    def _get_model_config(self, model_name: str) -> ModelConfig:
        """Retrieve model configuration from global ATHOS config.

        Args:
            model_name: Name of the model in config.models

        Returns:
            ModelConfig for the requested model

        Raises:
            RuntimeError: If full_config is not available
            ValueError: If model_name is not found in config
        """
        if self._full_config is None:
            raise RuntimeError("ATHOS configuration is required to access model config")

        try:
            return self._full_config.models[model_name]
        except KeyError as exc:
            raise ValueError(
                f"Unknown model '{model_name}' configured for {self.name}"
            ) from exc

    def _get_tool_config(self, tool_name: str) -> ToolConfig:
        """Retrieve tool configuration from global ATHOS config.

        Args:
            tool_name: Name of the tool in config.tools

        Returns:
            ToolConfig for the requested tool

        Raises:
            RuntimeError: If full_config is not available
            ValueError: If tool_name is not found in config
        """
        if self._full_config is None:
            raise RuntimeError("ATHOS configuration is required to access tool config")

        try:
            return self._full_config.tools[tool_name]
        except KeyError as exc:
            raise ValueError(
                f"Unknown tool '{tool_name}' configured for {self.name}"
            ) from exc

    def _get_mcp_server_config(self, server_name: str) -> MCPServerConfig:
        """Retrieve MCP server configuration from global ATHOS config.

        Args:
            server_name: Name of the MCP server in config.mcp_servers

        Returns:
            MCPServerConfig for the requested server

        Raises:
            RuntimeError: If full_config is not available
            ValueError: If server_name is not found in config
        """
        if self._full_config is None:
            raise RuntimeError(
                "ATHOS configuration is required to access MCP server config"
            )

        try:
            return self._full_config.mcp_servers[server_name]
        except KeyError as exc:
            raise ValueError(
                f"Unknown MCP server '{server_name}' configured for {self.name}"
            ) from exc


__all__ = ["BaseLangGraphFlow"]
