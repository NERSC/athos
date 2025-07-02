import yaml
from pathlib import Path
from typing import Union

from pydantic import ValidationError

from athos.config.models import (
    AthosConfig,
    ToolConfig,
    ModelConfig,
    MCPType,
    MCPServerConfig,
    ExecutionFlowType,
    ExecutionFlowConfig
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

        try:
            # Let Pydantic handle parsing and validation
            return AthosConfig.model_validate(config_data)
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e}")
