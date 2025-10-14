import os
import re
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, SecretStr


DEFAULT_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:\s]+):-([^}]+)\}")


def expand_env(value: Optional[str]) -> Optional[str]:
    """Expand environment variables including default syntax."""
    if value is None:
        return None

    def repl(match: re.Match) -> str:
        var, default = match.group(1), match.group(2)
        return os.environ.get(var, default)

    return os.path.expandvars(DEFAULT_ENV_VAR_PATTERN.sub(repl, value))


class MCPType(str, Enum):
    """Supported MCP server types"""
    MCP_STDIO = "mcp_stdio"
    MCP_SSE = "mcp_sse"


class ModelConfig(BaseModel):
    """Configuration for AI models"""
    model_config = ConfigDict(extra='forbid')

    description: Optional[str] = Field(
        default=None,
        description="Human-readable summary of the model's purpose",
    )
    model_id: str
    api_key: Optional[SecretStr] = Field(default=None, description="API key for model access")
    api_base: Optional[str] = Field(default=None, description="Base URL for API")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=1024, gt=0, description="Maximum tokens to generate")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for model")

    @field_validator('api_key', 'api_base', mode='before')
    @classmethod
    def expand_env_vars(cls, v: Optional[str]) -> Optional[str]:
        """Expand environment variables for API configuration fields."""
        return expand_env(v)

    @field_validator('api_base')
    @classmethod
    def validate_api_base(cls, v: Optional[str]) -> Optional[str]:
       if v and not v.startswith(('http://', 'https://')):
           raise ValueError('api_base must be a valid HTTP/HTTPS URL')
       return v


class MCPServerConfig(BaseModel):
    """Configuration for MCP server connection"""
    model_config = ConfigDict(extra='forbid')

    description: Optional[str] = Field(
        default=None,
        description="Human-readable summary of the MCP server",
    )
    mcp_type: MCPType
    # For stdio transport
    command: Optional[str] = Field(default=None, description="Command to execute for stdio MCP")
    args: List[str] = Field(default_factory=list, description="Arguments for stdio command")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")

    # For SSE transport
    url: Optional[str] = Field(default=None, description="URL for SSE MCP server")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for SSE")
    instructions: Optional[str] = Field(
        default=None,
        description="Additional instructions to include for tools from this MCP server",
    )

    @field_validator('url', mode='before')
    @classmethod
    def expand_url_env_vars(cls, v: Optional[str]) -> Optional[str]:
        """Expand environment variables in URL field."""
        return expand_env(v)

    @field_validator('instructions', mode='before')
    @classmethod
    def expand_instructions_env_vars(cls, v: Optional[str]) -> Optional[str]:
        """Expand environment variables in instructions field."""
        return expand_env(v)

    @model_validator(mode='before')
    @classmethod
    def expand_dict_env_vars(cls, data: Any) -> Any:
        """Expand environment variables in env, headers and args."""
        if isinstance(data, dict):
            # Expand environment variables in env dictionary values
            if 'env' in data and isinstance(data['env'], dict):
                data['env'] = {
                    k: expand_env(v) if isinstance(v, str) else v
                    for k, v in data['env'].items()
                }

            # Expand environment variables in headers dictionary values
            if 'headers' in data and isinstance(data['headers'], dict):
                data['headers'] = {
                    k: expand_env(v) if isinstance(v, str) else v
                    for k, v in data['headers'].items()
                }

            # Expand environment variables in args list values
            if 'args' in data and isinstance(data['args'], list):
                data['args'] = [
                    expand_env(v) if isinstance(v, str) else v
                    for v in data['args']
                ]

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

    description: Optional[str] = Field(
        default=None,
        description="Human-readable summary of what the tool does",
    )
    callable_name: str = Field(description="Python callable name for the tool")
    module_path: str = Field(description="Python module path containing the tool callable")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool initialization parameters")
    is_class: bool = Field(
        default=True,
        description="Whether the callable is a class requiring instantiation",
    )

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
    """Base configuration for flows"""
    model_config = ConfigDict(extra='forbid')

    description: Optional[str] = Field(
        default=None,
        description="Human-readable summary of the flow",
    )
    type: str = Field(description="Flow type identifier")
    model: str = Field(description="Reference to model configuration")

class AthosConfig(BaseModel):
    """Main ATHOS configuration"""
    model_config = ConfigDict(extra='forbid')

    models: Dict[str, ModelConfig] = Field(default_factory=dict, description="Model configurations")
    tools: Dict[str, ToolConfig] = Field(default_factory=dict, description="Tool configurations")
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict, description="MCP server configurations")
    flows: Dict[str, BaseFlowConfig] = Field(default_factory=dict, description="Flow configurations")
    hpc_cluster_config: Optional[Dict[str, Any]] = Field(default=None, description="HPC cluster configuration")
    logging_config: Optional[Dict[str, Any]] = Field(default=None, description="Logging configuration")
    workspace_dir: str = Field(..., description="Root directory shared by tools/MCP servers")

    @field_validator("workspace_dir", mode="before")
    @classmethod
    def expand_workspace_env(cls, v: str) -> str:
        """Expand environment variables in workspace directory path."""
        return expand_env(v)

    @model_validator(mode='before')
    @classmethod
    def validate_and_construct_flows(cls, data: Any) -> Any:
        """Dynamically construct and validate flow configs based on registry"""
        if not isinstance(data, dict):
            return data

        from athos.core.flow_registry import FLOW_REGISTRY

        # Ensure built-in flows are registered
        import athos.flows.builtins  # noqa: F401 - register built-in flows

        flows = data.get('flows', {})
        if not flows:
            return data

        constructed_flows = {}

        for flow_name, flow_data in flows.items():
            # Extract flow type from raw data
            if isinstance(flow_data, dict):
                flow_type = flow_data.get('type')
                if not flow_type:
                    raise ValueError(f"Flow '{flow_name}' missing 'type' field")
            else:
                raise ValueError(f"Flow '{flow_name}' must be a dictionary with 'type' field")

            # Look up config class from registry
            if flow_type not in FLOW_REGISTRY:
                raise ValueError(f"Unknown flow type '{flow_type}' for flow '{flow_name}'. Available types: {list(FLOW_REGISTRY.keys())}")

            config_cls, _ = FLOW_REGISTRY[flow_type]

            # Dynamically construct the appropriate config
            try:
                flow_config = config_cls.model_validate(flow_data)
                constructed_flows[flow_name] = flow_config
            except Exception as e:
                raise ValueError(f"Invalid config for flow '{flow_name}' of type '{flow_type}': {e}")

        # Replace raw data with constructed configs
        data['flows'] = constructed_flows
        return data

    @model_validator(mode='after')
    def validate_references(self):
        """Validate that flows reference valid models, tools, and MCP servers"""
        return self._validate_references()

    def _validate_references(self):
        """Validate that flows reference valid models, tools, and MCP servers"""
        for flow_name, flow_config in self.flows.items():
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
