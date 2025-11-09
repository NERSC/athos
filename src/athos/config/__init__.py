import yaml
from pathlib import Path
from typing import Union, Dict, Any, Optional
import os

from pydantic import ValidationError

from athos.config.models import AthosConfig, expand_env

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

        ConfigLoader._resolve_prompt_paths(config_data, config_path.parent)

        try:
            # Let Pydantic handle parsing and validation
            return AthosConfig.model_validate(config_data)
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e}")

    @staticmethod
    def _resolve_prompt_paths(config_data: Dict[str, Any], config_dir: Path) -> None:
        """Resolve *_path fields to populate inline prompt strings."""

        def _read_prompt(path_value: Optional[str]) -> Optional[str]:
            if not path_value:
                return None

            expanded = expand_env(path_value)
            if expanded is None:
                return None

            prompt_path = Path(expanded)
            if not prompt_path.is_absolute():
                prompt_path = config_dir / prompt_path

            if not prompt_path.exists():
                raise FileNotFoundError(
                    f"Prompt file not found at '{prompt_path}'."
                )
            if not prompt_path.is_file():
                raise ValueError(
                    f"Prompt path '{prompt_path}' is not a file."
                )

            try:
                return prompt_path.read_text(encoding="utf-8")
            except OSError as exc:
                raise OSError(
                    f"Failed to read prompt file '{prompt_path}': {exc}"
                ) from exc

        models = config_data.get("models")
        if isinstance(models, dict):
            for model_cfg in models.values():
                if isinstance(model_cfg, dict) and "system_prompt_path" in model_cfg:
                    prompt = _read_prompt(model_cfg.get("system_prompt_path"))
                    if prompt is not None:
                        model_cfg["system_prompt"] = prompt

        flows = config_data.get("flows")
        if isinstance(flows, dict):
            for flow_cfg in flows.values():
                if not isinstance(flow_cfg, dict):
                    continue

                if "system_prompt_path" in flow_cfg:
                    prompt = _read_prompt(flow_cfg.get("system_prompt_path"))
                    if prompt is not None:
                        flow_cfg["system_prompt"] = prompt

                if "instructions_path" in flow_cfg:
                    instructions = _read_prompt(flow_cfg.get("instructions_path"))
                    if instructions is not None:
                        flow_cfg["instructions"] = instructions
