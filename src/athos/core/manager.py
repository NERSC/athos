import logging
from typing import Dict, List, Any
from importlib import import_module

from smolagents import OpenAIServerModel, Tool, MCPClient
from mcp import StdioServerParameters

from athos.config import (
    AthosConfig,
    ToolConfig,
    MCPType,
    MCPServerConfig,
    ConfigLoader
)

from athos.core.flows import BaseFlow
from athos.core.flow_registry import FLOW_REGISTRY, load_plugins as load_flow_plugins
from athos.core.tool_registry import TOOL_REGISTRY, load_plugins as load_tool_plugins
import athos.core.builtin_flows  # noqa: F401 - register built-in flows

# Module logger
logger = logging.getLogger(__name__)


class AthosManager:
    """Main ATHOS agent flow manager."""

    def __init__(self, config: AthosConfig):
        self.config = config
        self.models: Dict[str, OpenAIServerModel] = {}
        self.loaded_tools: Dict[str, Tool] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.flows: Dict[str, BaseFlow] = {}

        self._flow_plugins_loaded = False
        self._tool_plugins_loaded = False

        # Preload built-in flow types and any installed plugins
        load_flow_plugins()
        load_tool_plugins()
        self._flow_plugins_loaded = True
        self._tool_plugins_loaded = True

    def _create_mcp_client(self, name: str, mcp_config: MCPServerConfig) -> MCPClient:
        """Create and cache MCP client based on configuration"""
        if name in self.mcp_clients:
            return self.mcp_clients[name]

        if mcp_config.mcp_type == MCPType.MCP_STDIO:
            params = StdioServerParameters(
                command=mcp_config.command,
                args=mcp_config.args,
                env=mcp_config.env
            )
        elif mcp_config.mcp_type == MCPType.MCP_SSE:
            params = dict(
                url=mcp_config.url,
                headers=mcp_config.headers
            )
        else:
            raise ValueError(f"Unsupported MCP type {mcp_config.mcp_type}")

        mcp_client = MCPClient(params)
        self.mcp_clients[name] = mcp_client
        return mcp_client


    def _load_tool(self, name: str, tool_config: ToolConfig) -> Tool:
        """Load a regular tool from configuration or plugin registry."""
        if name in self.loaded_tools:
            return self.loaded_tools[name]

        try:
            # Check plugin registry first
            factory = TOOL_REGISTRY.get(name)
            if factory:
                tool_instance = factory(tool_config)
            else:
                module = import_module(tool_config.module_path)
                tool_class = getattr(module, tool_config.class_name)
                tool_instance = tool_class(**tool_config.parameters)

            self.loaded_tools[name] = tool_instance

            logger.info(f"Loaded regular tool: {name}")
            return tool_instance

        except Exception as e:
            logger.error(f"Failed to load tool {name}: {e}")
            raise

    def _get_or_create_model(self, name: str) -> OpenAIServerModel:
        """Retrieve existing model or create it from configuration."""
        if name in self.models:
            return self.models[name]

        model_config = self.config.models.get(name)
        if not model_config:
            raise ValueError(f"Unknown model: {name}")

        model = OpenAIServerModel(
            model_id=model_config.model_id,
            api_base=model_config.api_base,
            api_key=model_config.api_key.get_secret_value() if model_config.api_key else None,
        )
        self.models[name] = model
        logger.info(f"Initialized model: {name}")
        return model

    def _initialize_models(self):
        """Eagerly create all configured models."""
        for name in self.config.models.keys():
            self._get_or_create_model(name)

    def _ensure_plugins_loaded(self) -> None:
        """Load flow and tool plugins once."""
        if not self._flow_plugins_loaded:
            load_flow_plugins()
            self._flow_plugins_loaded = True
        if not self._tool_plugins_loaded:
            load_tool_plugins()
            self._tool_plugins_loaded = True

    def _get_or_create_flow(self, name: str) -> BaseFlow:
        """Retrieve existing flow or create it from configuration."""
        if name in self.flows:
            return self.flows[name]

        self._ensure_plugins_loaded()

        if name not in self.config.execution_flows:
            raise ValueError(f"Unknown execution flow: {name}")

        flow_config = self.config.execution_flows[name]

        entry = FLOW_REGISTRY.get(flow_config.type)
        if not entry:
            raise ValueError(f"Unknown execution flow type: {flow_config.type}")

        config_cls, factory = entry
        assert isinstance(flow_config, config_cls)
        flow = factory(flow_config, self)
        self.flows[name] = flow
        logger.info(f"Initialized execution flow: {name}")
        return flow

    def _initialize_flows(self):
        """Deprecated initialization method kept for backward compatibility."""
        self.preload_flows()

    async def execute_flow(self, flow_name: str, input_data: str) -> Any:
        """Execute a specific flow with input data"""
        try:
            flow = self._get_or_create_flow(flow_name)
        except ValueError:
            raise

        logger.info(f"Executing flow: {flow_name} with type: {type(flow)}")
        return await flow.execute(input_data)

    def list_flows(self) -> List[str]:
        """List all available execution flows"""
        return list(self.config.execution_flows.keys())


    def describe_flow(self, flow_name: str) -> Dict[str, Any]:
        """Return full configuration details for a flow."""
        if flow_name not in self.config.execution_flows:
            raise ValueError(f"Unknown execution flow: {flow_name}")

        flow_cfg = self.config.execution_flows[flow_name]

        details = {
            "name": flow_name,
            "config": flow_cfg.model_dump(exclude_none=True),
            "model_config": self.config.models[flow_cfg.model].model_dump(exclude_none=True),
        }

        tools = getattr(flow_cfg, "tools", [])
        if tools:
            details["tool_configs"] = {
                name: self.config.tools[name].model_dump(exclude_none=True)
                for name in tools
            }

        mcp_servers = getattr(flow_cfg, "mcp_servers", [])
        if mcp_servers:
            details["mcp_server_configs"] = {
                name: self.config.mcp_servers[name].model_dump(exclude_none=True)
                for name in mcp_servers
            }

        return details

    def preload_flows(self) -> None:
        """Eagerly create all configured flows."""
        for name in self.config.execution_flows.keys():
            self._get_or_create_flow(name)

    def close(self):
        """Clean up resources, particularly MCP clients"""
        for client_name, client in self.mcp_clients.items():
            try:
                client.disconnect()
                logger.info(f"Closed MCP client: {client_name}")
            except Exception as e:
                logger.warning(f"Error closing MCP client {client_name}: {e}")

        self.mcp_clients.clear()
        logger.info("AthosManager cleanup completed")

# Example usage and factory function
from athos.logging_utils import configure_logging


def create_athos_manager(config_path: str) -> AthosManager:
    """Factory function to create ATHOS agent from configuration file"""
    config = ConfigLoader.load_config(config_path)
    if config.logging_config is not None:
        configure_logging(config.logging_config)
    return AthosManager(config)
