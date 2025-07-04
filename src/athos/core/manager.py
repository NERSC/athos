import logging
from typing import Dict, List, Any

from smolagents import OpenAIServerModel, Tool, MCPClient
from mcp import StdioServerParameters

from athos.config import (
    AthosConfig,
    ToolConfig,
    MCPType,
    MCPServerConfig,
    ExecutionFlowType,
    ConfigLoader
)

from athos.core.flows import BaseFlow
from athos.core.flow_registry import FLOW_REGISTRY, load_plugins
import athos.core.builtin_flows  # noqa: F401 - register built-in flows

# Module logger
logger = logging.getLogger(__name__)


class AthosManager:
    """Main ATHOS agent flow manager.
    
    TODOs:
    - remove execution functionality from this class
    - make flow initialization more generic, no if/else
    - consider lazy initialization of flows, tools, etc.
    - make model types flexible and/or fully optional
    """

    def __init__(self, config: AthosConfig):
        self.config = config
        self.models: Dict[str, OpenAIServerModel] = {}
        self.loaded_tools: Dict[str, Tool] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.flows: Dict[str, BaseFlow] = {}

        self._plugins_loaded = False

        # Preload built-in flow types and any installed plugins
        load_plugins()
        self._plugins_loaded = True

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
        logger.info(f"Create MCP client: {params}")
        self.mcp_clients[name] = mcp_client
        return mcp_client
    

    def _load_tool(self, name: str, tool_config: ToolConfig) -> Tool:
        """Load a regular tool from configuration"""
        if name in self.loaded_tools:
            return self.loaded_tools[name]

        try:
            # Load regular tool
            module = __import__(tool_config.module_path, fromlist=[tool_config.class_name])
            tool_class = getattr(module, tool_config.class_name)

            # Instantiate tool with parameters
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
            api_key=model_config.api_key,
        )
        self.models[name] = model
        logger.info(f"Initialized model: {name}")
        return model

    def _initialize_models(self):
        """Eagerly create all configured models."""
        for name in self.config.models.keys():
            self._get_or_create_model(name)

    def _ensure_plugins_loaded(self) -> None:
        """Load flow plugins once."""
        if not self._plugins_loaded:
            load_plugins()
            self._plugins_loaded = True

    def _get_or_create_flow(self, name: str) -> BaseFlow:
        """Retrieve existing flow or create it from configuration."""
        if name in self.flows:
            return self.flows[name]

        self._ensure_plugins_loaded()

        if name not in self.config.execution_flows:
            raise ValueError(f"Unknown execution flow: {name}")

        flow_config = self.config.execution_flows[name]
        entry = FLOW_REGISTRY.get(flow_config.type.value)
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

    def get_flow_info(self, flow_name: str) -> Dict[str, Any]:
        """Get information about a specific flow"""
        if flow_name not in self.config.execution_flows:
            raise ValueError(f"Unknown execution flow: {flow_name}")

        flow_config = self.config.execution_flows[flow_name]
        return {
            "name": flow_name,
            "type": flow_config.type.value,
            "model": flow_config.model,
            "tools": getattr(flow_config, "tools", []),
            "mcp_servers": getattr(flow_config, "mcp_servers", []),
            "has_prompt_chain": getattr(flow_config, "prompt_chain", None) is not None
        }

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
