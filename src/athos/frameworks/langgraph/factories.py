"""Factory helpers for constructing LangGraph-compatible components."""

from __future__ import annotations

from importlib import import_module
import logging
from typing import Any, Dict, List, TYPE_CHECKING

from athos.config.models import MCPServerConfig, MCPType, ModelConfig, ToolConfig

if TYPE_CHECKING:  # pragma: no cover - used only for typing
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.tools import BaseTool
else:  # pragma: no cover - fall back to ``Any`` when langchain is not installed
    BaseLanguageModel = Any  # type: ignore
    BaseTool = Any  # type: ignore

try:  # pragma: no cover - optional dependency
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - defer import errors until runtime
    ChatOpenAI = None

logger = logging.getLogger(__name__)


class LangGraphMCPClient:
    """Lightweight placeholder for future LangGraph MCP integrations."""

    def __init__(self, name: str, cfg: MCPServerConfig) -> None:
        self.name = name
        self.config = cfg

    def get_tools(self) -> List[Any]:
        """Return tools exposed by the MCP server.

        The LangGraph integration does not yet fetch tools from MCP servers. The
        method returns an empty list so flows can continue bootstrapping while the
        full implementation is developed.
        """

        logger.debug(
            "LangGraph MCP client '%s' get_tools called - returning no tools (not yet implemented)",
            self.name,
        )
        return []

    def close(self) -> None:
        """Placeholder cleanup hook for future MCP clients."""

        logger.debug("LangGraph MCP client '%s' close called", self.name)


def build_model(cfg: ModelConfig) -> BaseLanguageModel:
    """Instantiate a LangChain chat model for LangGraph flows."""

    if ChatOpenAI is None:  # pragma: no cover - executed only without optional deps
        raise ImportError(
            "langchain-openai must be installed to build LangGraph models."
        )

    init_kwargs: Dict[str, Any] = {
        "model": cfg.model_id,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
    }
    if cfg.api_key:
        init_kwargs["api_key"] = cfg.api_key.get_secret_value()
    if cfg.api_base:
        init_kwargs["base_url"] = cfg.api_base
    if cfg.system_prompt:
        # ``ChatOpenAI`` supports providing a default system prompt via metadata.
        init_kwargs["default_system_prompt"] = cfg.system_prompt

    model = ChatOpenAI(**init_kwargs)
    logger.debug("Created LangGraph ChatOpenAI model for id '%s'", cfg.model_id)
    return model


def build_tool(cfg: ToolConfig) -> BaseTool:
    """Dynamically import and instantiate a LangChain tool."""

    module = import_module(cfg.module_path)
    tool_obj = getattr(module, cfg.callable_name)
    tool = tool_obj(**cfg.parameters) if cfg.is_class else tool_obj
    logger.debug(
        "Instantiated LangGraph tool '%s.%s' (is_class=%s)",
        cfg.module_path,
        cfg.callable_name,
        cfg.is_class,
    )
    return tool


def build_mcp_client(name: str, cfg: MCPServerConfig) -> LangGraphMCPClient:
    """Create a placeholder MCP client for LangGraph flows."""

    if cfg.mcp_type not in {MCPType.MCP_STDIO, MCPType.MCP_SSE}:  # pragma: no cover
        raise ValueError(f"Unsupported MCP type {cfg.mcp_type}")

    logger.info(
        "Created LangGraph MCP client '%s' of type '%s' (implementation pending)",
        name,
        cfg.mcp_type.value,
    )
    return LangGraphMCPClient(name, cfg)


__all__ = ["build_model", "build_tool", "build_mcp_client", "LangGraphMCPClient"]
