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

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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

        self._initialize_models()
        self._initialize_flows()

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

    def _initialize_models(self):
        """Initialize all configured models"""
        for name, model_config in self.config.models.items():
            model = OpenAIServerModel(
                model_id=model_config.model_id,
                api_base=model_config.api_base,
                api_key=model_config.api_key
            )
            self.models[name] = model
            logger.info(f"Initialized model: {name}")

    def _initialize_flows(self):
        """Initialize all configured execution flows"""
        load_plugins()
        for name, flow_config in self.config.execution_flows.items():
            entry = FLOW_REGISTRY.get(flow_config.type.value)
            if not entry:
                raise ValueError(f"Unknown execution flow type: {flow_config.type}")

            config_cls, factory = entry
            assert isinstance(flow_config, config_cls)
            flow = factory(flow_config, self)
            self.flows[name] = flow
            logger.info(f"Initialized execution flow: {name}")

    async def execute_flow(self, flow_name: str, input_data: str) -> Any:
        """Execute a specific flow with input data"""
        try:
            flow = self.flows[flow_name]
        except KeyError:
            raise ValueError(f"Unknown execution flow: {flow_name}")

        logger.info(f"Executing flow: {flow_name} with type: {type(flow)}")
        return await flow.execute(input_data)

    def list_flows(self) -> List[str]:
        """List all available execution flows"""
        return list(self.flows.keys())

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
def create_athos_manager(config_path: str) -> AthosManager:
    """Factory function to create ATHOS agent from configuration file"""
    config = ConfigLoader.load_config(config_path)
    return AthosManager(config)
