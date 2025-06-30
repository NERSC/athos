import logging
from typing import Dict, List, Any, Union

from smolagents import OpenAIServerModel, Tool
from mcp import StdioServerParameters
from smolagents.mcp_client import MCPClient

from athos.config import (
    AthosConfig,
    ToolConfig,
    ToolType,
    MCPType,
    MCPServerConfig,
    ExecutionFlowType,
    ConfigLoader
)

from athos.core.flows import BaseFlow, ChatbotFlow, CodeAgentFlow, ToolCallingAgentFlow

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

    def _create_mcp_client(self, mcp_config: MCPServerConfig) -> MCPClient:
        """Create and cache MCP client based on configuration"""
        if mcp_config.name in self.mcp_clients:
            return self.mcp_clients[mcp_config.name]
        
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
        self.mcp_clients[mcp_config.name] = mcp_client
        return mcp_client
    
        # # Create cache key based on config
        # if mcp_config.command:
        #     cache_key = f"stdio:{mcp_config.command}"
        #     if cache_key not in self.mcp_clients:
        #         params = StdioServerParameters(
        #             command=mcp_config.command,
        #             args=mcp_config.args,
        #             env=mcp_config.env
        #         )
        #         self.mcp_clients[cache_key] = MCPClient(params)
        #         logger.info(f"Created MCP stdio client: {cache_key}")
        # elif mcp_config.url:
        #     cache_key = f"sse:{mcp_config.url}"
        #     if cache_key not in self.mcp_clients:
        #         params = dict(
        #             url=mcp_config.url,
        #             headers=mcp_config.headers
        #         )
        #         self.mcp_clients[cache_key] = MCPClient(params)
        #         logger.info(f"Created MCP SSE client: {cache_key}")
        # else:
        #     raise ValueError("MCP config must specify either command or url")

        # return self.mcp_clients[cache_key]

    def _load_mcp_tools(self, tool_config: ToolConfig) -> List[Tool]:
        """Load tools from MCP server"""
        if not tool_config.mcp_config:
            raise ValueError(f"MCP tool {tool_config.name} missing mcp_config")

        try:
            mcp_client = self._create_mcp_client(tool_config.mcp_config)
            all_tools = list(mcp_client.get_tools())

            # If specific tool name specified, filter for it
            if tool_config.mcp_tool_name:
                filtered_tools = [t for t in all_tools if t.name == tool_config.mcp_tool_name]
                if not filtered_tools:
                    raise ValueError(f"Tool '{tool_config.mcp_tool_name}' not found in MCP server")
                return filtered_tools

            return all_tools
            
        except Exception as e:
            logger.error(f"Failed to load MCP tools for {tool_config.name}: {e}")
            raise

    def _load_tool(self, tool_config: ToolConfig) -> Union[Tool, List[Tool]]:
        """Load a tool from configuration (regular or MCP)
        
        TODO: remove MCP stuff from here, return only single tool.
        """
        if tool_config.name in self.loaded_tools:
            return self.loaded_tools[tool_config.name]

        try:
            if tool_config.tool_type == ToolType.REGULAR:
                # Existing regular tool loading logic
                module = __import__(tool_config.module_path, fromlist=[tool_config.class_name])
                tool_class = getattr(module, tool_config.class_name)

                # Instantiate tool with parameters
                tool_instance = tool_class(**tool_config.parameters)
                self.loaded_tools[tool_config.name] = tool_instance

                logger.info(f"Loaded regular tool: {tool_config.name}")
                return tool_instance

            elif tool_config.tool_type in [ToolType.MCP_STDIO, ToolType.MCP_SSE]:
                # New MCP tool loading logic
                mcp_tools = self._load_mcp_tools(tool_config)

                # Cache tools individually
                for tool in mcp_tools:
                    cache_key = f"{tool_config.name}:{tool.name}"
                    self.loaded_tools[cache_key] = tool

                logger.info(f"Loaded {len(mcp_tools)} MCP tools for: {tool_config.name}")
                return mcp_tools if len(mcp_tools) > 1 else mcp_tools[0]

            else:
                raise ValueError(f"Unknown tool type: {tool_config.tool_type}")

        except Exception as e:
            logger.error(f"Failed to load tool {tool_config.name}: {e}")
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
        for name, flow_config in self.config.execution_flows.items():
            model = self.models[flow_config.model]

            # TODO: improve this to have less duplication,
            # make more scalable / extensible

            if flow_config.type == ExecutionFlowType.CHATBOT:
                flow = ChatbotFlow(model, flow_config.system_prompt)

            elif flow_config.type == ExecutionFlowType.CODE_AGENT:
                mcp_servers = []
                for mcp_name in flow_config.mcp_servers:
                    logger.info(f"loading MCP server {mcp_name}")
                    mcp_config = self.config.mcp_servers[mcp_name]
                    # FINISHME
                    # loaded_mcp = 
                tools = []
                for tool_name in flow_config.tools:
                    logger.info(f"loading tool {tool_name}")
                    tool_config = self.config.tools[tool_name]
                    loaded_tool = self._load_tool(tool_config)

                    # Handle both single tools and lists of tools (from MCP)
                    if isinstance(loaded_tool, list):
                        tools.extend(loaded_tool)
                    else:
                        tools.append(loaded_tool)
                flow = CodeAgentFlow(model, tools)
                logger.info(f"Initialized CodeAgentFlow: {name}")
            elif flow_config.type == ExecutionFlowType.TOOL_CALLING_AGENT:
                tools = []
                for tool_name in flow_config.tools:
                    logger.info(f"loading tool {tool_name}")
                    tool_config = self.config.tools[tool_name]
                    loaded_tool = self._load_tool(tool_config)

                    # Handle both single tools and lists of tools (from MCP)
                    if isinstance(loaded_tool, list):
                        tools.extend(loaded_tool)
                    else:
                        tools.append(loaded_tool)
                flow = ToolCallingAgentFlow(model, tools)
                logger.info(f"Initialized ToolCallingAgentFlow: {name}")

            elif flow_config.type == ExecutionFlowType.PROMPT_CHAIN:
                raise NotImplementedError
                # flow = PromptChainFlow(model, flow_config.prompt_chain)

            else:
                raise ValueError(f"Unknown execution flow type: {flow_config.type}")

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
            "name": flow_config.name,
            "type": flow_config.type.value,
            "model": flow_config.model,
            "tools": flow_config.tools,
            "has_prompt_chain": flow_config.prompt_chain is not None
        }

    def close(self):
        """Clean up resources, particularly MCP clients"""
        for client_key, client in self.mcp_clients.items():
            try:
                # Note: MCPClient may not have explicit close method
                # This is a placeholder for proper cleanup if needed
                if hasattr(client, 'close'):
                    client.close()
                logger.info(f"Closed MCP client: {client_key}")
            except Exception as e:
                logger.warning(f"Error closing MCP client {client_key}: {e}")

        self.mcp_clients.clear()
        logger.info("AthosManager cleanup completed")

# Example usage and factory function
def create_athos_manager(config_path: str) -> AthosManager:
    """Factory function to create ATHOS agent from configuration file"""
    config = ConfigLoader.load_config(config_path)
    return AthosManager(config)
