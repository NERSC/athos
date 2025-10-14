import yaml
from pathlib import Path
from typing import Union, Dict, Any, Optional
import os

from pydantic import ValidationError

from athos.config.models import (
    AthosConfig,
    ToolConfig,
    ModelConfig,
    MCPType,
    MCPServerConfig,
    BaseFlowConfig,
)
from athos.flows import ChatbotFlowConfig, AgentFlowConfig

class ConfigLoader:
    """Loads and validates YAML configuration files"""
    
    @staticmethod
    def _deep_update(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
        for key, value in overrides.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                ConfigLoader._deep_update(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def load_config(
        config_path: Union[str, Path], overrides: Optional[Dict[str, Any]] = None
    ) -> AthosConfig:
        """Load configuration from YAML file and apply overrides"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        # On some systems running as root, os.access may still succeed even if
        # permission bits deny reading. Check the file mode explicitly.
        if not os.access(config_path, os.R_OK) or (config_path.stat().st_mode & 0o444) == 0:
            raise PermissionError(f"Configuration file not readable: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f) or {}

        if overrides:
            ConfigLoader._deep_update(config_data, overrides)

        try:
            # Let Pydantic handle parsing and validation
            return AthosConfig.model_validate(config_data)
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e}")
