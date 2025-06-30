from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

class ExecutionFlowType(Enum):
    """Supported execution flow types"""
    CHATBOT = "chatbot"
    CODE_AGENT = "code_agent"
    PROMPT_CHAIN = "prompt_chain"
    TOOL_CALLING_AGENT = "tool_calling_agent"

class ToolType(Enum):
    """Supported tool types"""
    REGULAR = "regular"
    MCP_STDIO = "mcp_stdio"
    MCP_SSE = "mcp_sse"

class MCPType(Enum):
    """Supported MCP server types"""
    MCP_STDIO = "mcp_stdio"
    MCP_SSE = "mcp_sse"

@dataclass
class ModelConfig:
    """Configuration for AI models"""
    name: str
    model_id: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    system_prompt: Optional[str] = None

@dataclass
class MCPServerConfig:
    """Configuration for MCP server connection"""
    name: str
    mcp_type: MCPType
    # For stdio transport
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    
    # For SSE transport
    url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class ToolConfig:
    """Configuration for tools (regular and MCP)"""
    name: str
    tool_type: ToolType = ToolType.REGULAR
    
    # Regular tool fields
    class_name: Optional[str] = None
    module_path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # MCP tool fields
    mcp_config: Optional[MCPServerConfig] = None
    mcp_tool_name: Optional[str] = None  # Specific tool name from MCP server

@dataclass
class ExecutionFlowConfig:
    """Configuration for execution flows"""
    name: str
    type: ExecutionFlowType
    model: str
    mcp_servers: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    prompt_chain: Optional[List[Dict[str, str]]] = None
    system_prompt: Optional[str] = None
    max_iterations: int = 10

@dataclass
class AthosConfig:
    """Main ATHOS configuration"""
    models: Dict[str, ModelConfig]
    tools: Dict[str, ToolConfig]
    mcp_servers: Dict[str, MCPServerConfig]
    execution_flows: Dict[str, ExecutionFlowConfig]
    hpc_cluster_config: Optional[Dict[str, Any]] = None
    logging_config: Optional[Dict[str, Any]] = None