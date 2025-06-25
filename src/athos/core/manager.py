import logging
from typing import Dict, List, Any

from smolagents import OpenAIServerModel, Tool

from athos.config import (
    AthosConfig,
    ToolConfig,
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
        self.flows: Dict[str, BaseFlow] = {}
        
        self._initialize_models()
        self._initialize_flows()

    def _load_tool(self, tool_config: ToolConfig) -> Tool:
        """Load a tool from configuration"""
        if tool_config.name in self.loaded_tools:
            return self.loaded_tools[tool_config.name]
        
        try:
            # Dynamic import of tool class
            module = __import__(tool_config.module_path, fromlist=[tool_config.class_name])
            tool_class = getattr(module, tool_config.class_name)
            
            # Instantiate tool with parameters
            tool_instance = tool_class(**tool_config.parameters)
            self.loaded_tools[tool_config.name] = tool_instance
            
            logger.info(f"Loaded tool: {tool_config.name}")
            return tool_instance
            
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
            
            if flow_config.type == ExecutionFlowType.CHATBOT:
                flow = ChatbotFlow(model, flow_config.system_prompt)
            
            elif flow_config.type == ExecutionFlowType.CODE_AGENT:
                tools = []
                for tool_name in flow_config.tools:
                    logger.info(f"loading tool {tool_name}")
                    tool_config = self.config.tools[tool_name]
                    tool = self._load_tool(tool_config)
                    tools.append(tool)
                flow = CodeAgentFlow(model, tools)
                logger.info(f"Initialized CodeAgentFlow: {name}")
            elif flow_config.type == ExecutionFlowType.TOOL_CALLING_AGENT:
                tools = []
                for tool_name in flow_config.tools:
                    logger.info(f"loading tool {tool_name}")
                    tool_config = self.config.tools[tool_name]
                    tool = self._load_tool(tool_config)
                    tools.append(tool)
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

# Example usage and factory function
def create_athos_manager(config_path: str) -> AthosManager:
    """Factory function to create ATHOS agent from configuration file"""
    config = ConfigLoader.load_config(config_path)
    return AthosManager(config)
