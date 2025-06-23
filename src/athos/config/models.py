from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

class ExecutionFlowType(Enum):
    """Supported execution flow types"""
    CHATBOT = "chatbot"
    CODE_AGENT = "code_agent"
    PROMPT_CHAIN = "prompt_chain"

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
class ToolConfig:
    """Configuration for tools"""
    name: str
    class_name: str
    module_path: str
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionFlowConfig:
    """Configuration for execution flows"""
    name: str
    type: ExecutionFlowType
    model: str
    tools: List[str] = field(default_factory=list)
    prompt_chain: Optional[List[Dict[str, str]]] = None
    system_prompt: Optional[str] = None
    max_iterations: int = 10

@dataclass
class AthosConfig:
    """Main ATHOS configuration"""
    models: Dict[str, ModelConfig]
    tools: Dict[str, ToolConfig]
    execution_flows: Dict[str, ExecutionFlowConfig]
    hpc_cluster_config: Optional[Dict[str, Any]] = None
    logging_config: Optional[Dict[str, Any]] = None