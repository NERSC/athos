import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from athos.config.models import (
    AthosConfig,
    ModelConfig,
    ToolConfig,
    MCPServerConfig,
    ExecutionFlowConfig,
    ExecutionFlowType,
    ToolType,
    MCPType
)

class ConfigLoader:
    """Loads and validates YAML configuration files"""
    
    @staticmethod
    def load_config(config_path: Union[str, Path]) -> AthosConfig:
        """Load configuration from YAML file"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        config = ConfigLoader._parse_config(config_data)
        ConfigLoader._validate_config(config)
        return config
    
    @staticmethod
    def _expand_env_var(var: str) -> str:
        # Replace ${VAR_NAME} with environment variable value
        def replace_env_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                raise ValueError(f"Configuration environment variable '{var_name}' is not set")
            return env_value
        return re.sub(r'\$\{([^}]+)\}', replace_env_var, var)
    
    @staticmethod
    def _parse_config(config_data: Dict[str, Any]) -> AthosConfig:
        """Parse configuration data into AthosConfig object"""
        # Parse models
        models = {}
        for name, model_data in config_data.get('models', {}).items():
            models[name] = ModelConfig(
                name=name,
                model_id=model_data['model_id'],
                api_key=ConfigLoader._expand_env_var(model_data.get('api_key')),
                api_base=ConfigLoader._expand_env_var(model_data.get('api_base')),
                temperature=model_data.get('temperature', 0.7),
                max_tokens=model_data.get('max_tokens', 1024),
                system_prompt=model_data.get('system_prompt')
            )

        # Parse MCP servers
        mcp_servers = {}
        for name, mcp_data in config_data.get('mcp_servers', {}).items():
            mcp_type = MCPType(mcp_data.get('mcp_type', 'mcp_stdio'))
            # Expand environment variables in MCP config
            env_vars = {}
            for key, value in mcp_data.get('env', {}).items():
                env_vars[key] = ConfigLoader._expand_env_var(value) if isinstance(value, str) else value

            headers = {}
            for key, value in mcp_data.get('headers', {}).items():
                headers[key] = ConfigLoader._expand_env_var(value) if isinstance(value, str) else value

            mcp_servers[name] = MCPServerConfig(
                name=name,
                mcp_type=mcp_type,
                command=mcp_data.get('command'),
                args=mcp_data.get('args', []),
                env=env_vars,
                url=ConfigLoader._expand_env_var(mcp_data.get('url')) if mcp_data.get('url') else None,
                headers=headers
            )

        # Parse tools
        tools = {}
        for name, tool_data in config_data.get('tools', {}).items():
            tool_type = ToolType(tool_data.get('tool_type', 'regular'))
            
            # Parse MCP config if present
            # TODO: remove this from tools
            mcp_config = None
            if 'mcp_config' in tool_data:
                mcp_data = tool_data['mcp_config']
                # Expand environment variables in MCP config
                env_vars = {}
                for key, value in mcp_data.get('env', {}).items():
                    env_vars[key] = ConfigLoader._expand_env_var(value) if isinstance(value, str) else value
                
                headers = {}
                for key, value in mcp_data.get('headers', {}).items():
                    headers[key] = ConfigLoader._expand_env_var(value) if isinstance(value, str) else value
                
                mcp_config = MCPServerConfig(
                    command=mcp_data.get('command'),
                    args=mcp_data.get('args', []),
                    env=env_vars,
                    url=ConfigLoader._expand_env_var(mcp_data.get('url')) if mcp_data.get('url') else None,
                    headers=headers
                )
            
            tools[name] = ToolConfig(
                name=name,
                tool_type=tool_type,
                class_name=tool_data.get('class_name'),
                module_path=tool_data.get('module_path'),
                parameters=tool_data.get('parameters', {}),
                mcp_config=mcp_config,
                mcp_tool_name=tool_data.get('mcp_tool_name')
            )
        
        # Parse execution flows
        execution_flows = {}
        for name, flow_data in config_data.get('execution_flows', {}).items():
            flow_type = ExecutionFlowType(flow_data['type'])
            execution_flows[name] = ExecutionFlowConfig(
                name=name,
                type=flow_type,
                model=flow_data['model'],
                mcp_servers=flow_data.get('mcp_servers', []),
                tools=flow_data.get('tools', []),
                prompt_chain=flow_data.get('prompt_chain'),
                system_prompt=flow_data.get('system_prompt'),
                max_iterations=flow_data.get('max_iterations', 10)
            )
        
        return AthosConfig(
            models=models,
            tools=tools,
            mcp_servers=mcp_servers,
            execution_flows=execution_flows,
            hpc_cluster_config=config_data.get('hpc_cluster_config'),
            logging_config=config_data.get('logging_config')
        )
    
    @staticmethod
    def _validate_config(config: AthosConfig) -> None:
        """Validate the parsed configuration"""
        # Validate MCP configurations
        for mcp_name, mcp_config in config.mcp_servers.items():
            ConfigLoader._validate_mcp_config(mcp_config)

        # Validate tool configurations
        for tool_name, tool_config in config.tools.items():
            ConfigLoader._validate_tool_config(tool_config)
        
        # Validate execution flows reference valid MCP servers, tools, and models
        for flow_name, flow_config in config.execution_flows.items():
            if flow_config.model not in config.models:
                raise ValueError(f"Flow '{flow_name}' references unknown model '{flow_config.model}'")

            for mcp_name in flow_config.mcp_servers:
                if mcp_name not in config.mcp_servers:
                    raise ValueError(f"Flow '{flow_name}' references unknown MCP '{mcp_name}")
            
            for tool_name in flow_config.tools:
                if tool_name not in config.tools:
                    raise ValueError(f"Flow '{flow_name}' references unknown tool '{tool_name}'")

    @staticmethod
    def _validate_mcp_config(mcp_config: MCPServerConfig) -> None:
        """Validate MCP server configuration"""
        if mcp_config.mcp_type == MCPType.MCP_STDIO and not mcp_config.command:
            raise ValueError(f"MCP stdio server '{mcp_config.name}' missing command in config")
    
        if mcp_config.mcp_type == MCPType.MCP_SSE and not mcp_config.url:
            raise ValueError(f"MCP SSE server '{mcp_config.name}' missing url in config")
    
        if mcp_config.mcp_type not in [MCPType.MCP_SSE, MCPType.MCP_STDIO]:
            raise ValueError(f"Unknown MCP server type: {mcp_config.mcp_type}")

    @staticmethod
    def _validate_tool_config(tool_config: ToolConfig) -> None:
        """Validate tool configuration"""
        if tool_config.tool_type == ToolType.REGULAR:
            if not tool_config.class_name or not tool_config.module_path:
                raise ValueError(f"Regular tool '{tool_config.name}' missing class_name or module_path")
        
        elif tool_config.tool_type in [ToolType.MCP_STDIO, ToolType.MCP_SSE]:
            if not tool_config.mcp_config:
                raise ValueError(f"MCP tool '{tool_config.name}' missing mcp_config")
            
            if tool_config.tool_type == ToolType.MCP_STDIO and not tool_config.mcp_config.command:
                raise ValueError(f"MCP stdio tool '{tool_config.name}' missing command in mcp_config")
            
            if tool_config.tool_type == ToolType.MCP_SSE and not tool_config.mcp_config.url:
                raise ValueError(f"MCP SSE tool '{tool_config.name}' missing url in mcp_config")
        
        else:
            raise ValueError(f"Unknown tool type: {tool_config.tool_type}")