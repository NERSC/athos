import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from athos.config.models import (
    AthosConfig,
    ModelConfig,
    ToolConfig,
    ExecutionFlowConfig,
    ExecutionFlowType
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
        
        return ConfigLoader._parse_config(config_data)
    
    @staticmethod
    def _expand_env_var(var: str) -> str:
        # Replace ${VAR_NAME} with environment variable value
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Return original if env var not found
        
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
        
        # Parse tools
        tools = {}
        for name, tool_data in config_data.get('tools', {}).items():
            tools[name] = ToolConfig(
                name=name,
                class_name=tool_data['class_name'],
                module_path=tool_data['module_path'],
                parameters=tool_data.get('parameters', {})
            )
        
        # Parse execution flows
        execution_flows = {}
        for name, flow_data in config_data.get('execution_flows', {}).items():
            flow_type = ExecutionFlowType(flow_data['type'])
            execution_flows[name] = ExecutionFlowConfig(
                name=name,
                type=flow_type,
                model=flow_data['model'],
                tools=flow_data.get('tools', []),
                prompt_chain=flow_data.get('prompt_chain'),
                system_prompt=flow_data.get('system_prompt'),
                max_iterations=flow_data.get('max_iterations', 10)
            )
        
        return AthosConfig(
            models=models,
            tools=tools,
            execution_flows=execution_flows,
            hpc_cluster_config=config_data.get('hpc_cluster_config'),
            logging_config=config_data.get('logging_config')
        )