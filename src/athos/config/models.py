import os
import re
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Annotated, Type
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing_extensions import Literal

class ExecutionFlowType(str, Enum):
    """Supported execution flow types"""
    CHATBOT = "chatbot"
    AGENT = "agent"
    PROMPT_CHAIN = "prompt_chain"


class AgentType(str, Enum):
    """Supported agent implementations"""
    CODE = "code"
    TOOL_CALLING = "tool_calling"

class MCPType(str, Enum):
    """Supported MCP server types"""
    MCP_STDIO = "mcp_stdio"
    MCP_SSE = "mcp_sse"

class ModelConfig(BaseModel):
    """Configuration for AI models"""
    model_config = ConfigDict(extra='forbid')

    model_id: str
    api_key: Optional[str] = Field(default=None, description="API key for model access")
    api_base: Optional[str] = Field(default=None, description="Base URL for API")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=1024, gt=0, description="Maximum tokens to generate")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for model")

    @field_validator('api_key', 'api_base', mode='before')
    @classmethod
    def expand_env_vars(cls, v: Optional[str]) -> Optional[str]:
        """Expand environment variables for API configuration fields."""
        return os.path.expandvars(v) if v else None

    @field_validator('api_base')
    @classmethod
    def validate_api_base(cls, v: Optional[str]) -> Optional[str]:
       if v and not v.startswith(('http://', 'https://')):
           raise ValueError('api_base must be a valid HTTP/HTTPS URL')
       return v

class MCPServerConfig(BaseModel):
    """Configuration for MCP server connection"""
    model_config = ConfigDict(extra='forbid')

    mcp_type: MCPType
    # For stdio transport
    command: Optional[str] = Field(default=None, description="Command to execute for stdio MCP")
    args: List[str] = Field(default_factory=list, description="Arguments for stdio command")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")

    # For SSE transport
    url: Optional[str] = Field(default=None, description="URL for SSE MCP server")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for SSE")

    @field_validator('url', mode='before')
    @classmethod
    def expand_url_env_vars(cls, v: Optional[str]) -> Optional[str]:
        """Expand environment variables in URL field."""
        return os.path.expandvars(v) if v else None

    @model_validator(mode='before')
    @classmethod
    def expand_dict_env_vars(cls, data: Any) -> Any:
        """Expand environment variables in env and headers dictionaries."""
        if isinstance(data, dict):
            # Expand environment variables in env dictionary values
            if 'env' in data and isinstance(data['env'], dict):
                data['env'] = {k: os.path.expandvars(v) if isinstance(v, str) else v
                              for k, v in data['env'].items()}

            # Expand environment variables in headers dictionary values
            if 'headers' in data and isinstance(data['headers'], dict):
                data['headers'] = {k: os.path.expandvars(v) if isinstance(v, str) else v
                                  for k, v in data['headers'].items()}
        return data

    @model_validator(mode='after')
    def validate_mcp_config(self):
       if self.mcp_type == MCPType.MCP_STDIO and not self.command:
           raise ValueError("MCP stdio server requires command")
       if self.mcp_type == MCPType.MCP_SSE and not self.url:
           raise ValueError("MCP SSE server requires url")
       return self

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
       if v and not v.startswith(('http://', 'https://')):
           raise ValueError('url must be a valid HTTP/HTTPS URL')
       return v

class ToolConfig(BaseModel):
    """Configuration for regular tools only"""
    model_config = ConfigDict(extra='forbid')

    class_name: str = Field(description="Python class name for the tool")
    module_path: str = Field(description="Python module path containing the tool class")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool initialization parameters")

    @field_validator('module_path')
    @classmethod
    def validate_module_path(cls, v: str) -> str:
        if not v:
            raise ValueError('module_path cannot be empty')
        # Each component must be a valid Python identifier
        for component in v.split("."):
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', component):
                raise ValueError('module_path must be a valid Python module path')
        return v

class BaseFlowConfig(BaseModel):
    """Base configuration for execution flows"""
    model_config = ConfigDict(extra='forbid')

    type: ExecutionFlowType
    model: str = Field(description="Reference to model configuration")


class ChatbotFlowConfig(BaseFlowConfig):
    """Configuration for ChatbotFlow"""

    type: Literal[ExecutionFlowType.CHATBOT]
    system_prompt: Optional[str] = Field(default=None, description="System prompt override")
    max_iterations: int = Field(default=10, gt=0, description="Maximum execution iterations")


class AgentFlowConfig(BaseFlowConfig):
    """Configuration for AgentFlow"""

    type: Literal[ExecutionFlowType.AGENT]
    agent_type: AgentType = Field(default=AgentType.CODE, description="Underlying agent implementation")
    mcp_servers: List[str] = Field(default_factory=list, description="List of MCP server names")
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    max_iterations: int = Field(default=10, gt=0, description="Maximum execution iterations")


class PromptChainFlowConfig(BaseFlowConfig):
    """Configuration for PromptChainFlow"""

    type: Literal[ExecutionFlowType.PROMPT_CHAIN]
    prompt_chain: Optional[List[Dict[str, str]]] = Field(default=None, description="Prompt chain configuration")


FlowConfig = Annotated[
    Union[
        ChatbotFlowConfig,
        AgentFlowConfig,
        PromptChainFlowConfig,
    ],
    Field(discriminator='type')
]

class AthosConfig(BaseModel):
    """Main ATHOS configuration"""
    model_config = ConfigDict(extra='forbid')

    models: Dict[str, ModelConfig] = Field(default_factory=dict, description="Model configurations")
    tools: Dict[str, ToolConfig] = Field(default_factory=dict, description="Tool configurations")
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict, description="MCP server configurations")
    execution_flows: Dict[str, FlowConfig] = Field(default_factory=dict, description="Execution flow configurations")
    hpc_cluster_config: Optional[Dict[str, Any]] = Field(default=None, description="HPC cluster configuration")
    logging_config: Optional[Dict[str, Any]] = Field(default=None, description="Logging configuration")

    @model_validator(mode='after')
    def validate_references(self):
       """Validate that execution flows reference valid models, tools, and MCP servers"""
       for flow_name, flow_config in self.execution_flows.items():
           # Validate model reference
           if flow_config.model not in self.models:
               raise ValueError(
                   f"Flow '{flow_name}' references unknown model '{flow_config.model}'"
               )

           # Validate MCP server references if present
           mcp_servers = getattr(flow_config, "mcp_servers", [])
           for mcp_name in mcp_servers:
               if mcp_name not in self.mcp_servers:
                   raise ValueError(
                       f"Flow '{flow_name}' references unknown MCP server '{mcp_name}'"
                   )

           # Validate tool references if present
           tools = getattr(flow_config, "tools", [])
           for tool_name in tools:
               if tool_name not in self.tools:
                   raise ValueError(
                       f"Flow '{flow_name}' references unknown tool '{tool_name}'"
                   )

       return self
