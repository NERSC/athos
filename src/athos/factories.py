"""Utility factory functions for constructing models, tools and MCP clients."""

from importlib import import_module
from typing import Dict
import logging

from smolagents import OpenAIServerModel, Tool, MCPClient
from mcp import StdioServerParameters

from athos.config.models import ModelConfig, ToolConfig, MCPServerConfig, MCPType

logger = logging.getLogger(__name__)


def build_model(cfg: ModelConfig) -> OpenAIServerModel:
    """Instantiate an :class:`OpenAIServerModel` from configuration."""
    return OpenAIServerModel(
        model_id=cfg.model_id,
        api_base=cfg.api_base,
        api_key=cfg.api_key.get_secret_value() if cfg.api_key else None,
    )


def build_tool(cfg: ToolConfig) -> Tool:
    """Dynamically import and instantiate a tool from configuration."""
    module = import_module(cfg.module_path)
    tool_cls = getattr(module, cfg.class_name)
    return tool_cls(**cfg.parameters)


def build_mcp_client(name: str, cfg: MCPServerConfig) -> MCPClient:
    """Create an MCP client based on configuration."""
    if cfg.mcp_type == MCPType.MCP_STDIO:
        params = StdioServerParameters(command=cfg.command, args=cfg.args, env=cfg.env)
    elif cfg.mcp_type == MCPType.MCP_SSE:
        params = dict(url=cfg.url, headers=cfg.headers)
    else:
        raise ValueError(f"Unsupported MCP type {cfg.mcp_type}")
    logger.info("Created MCP client '%s'", name)
    return MCPClient(params)

