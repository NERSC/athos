"""Runtime helpers to construct and execute flows without a manager."""

from typing import Any, Dict
import logging

from athos.config import AthosConfig, ConfigLoader
from athos.logging_utils import configure_logging
from athos.flows import BaseFlow
from athos.core.flow_registry import FLOW_REGISTRY, load_plugins
from athos.utils.workspace import get_workspace
import athos.flows.builtins  # noqa: F401 - register built-in flows

logger = logging.getLogger(__name__)


def build_flow(flow_name: str, config: AthosConfig) -> BaseFlow:
    """Construct a flow instance from the given configuration."""
    load_plugins()

    if flow_name not in config.execution_flows:
        raise ValueError(f"Unknown execution flow: {flow_name}")

    flow_cfg = config.execution_flows[flow_name]
    entry = FLOW_REGISTRY.get(flow_cfg.type)
    if not entry:
        raise ValueError(f"Unknown execution flow type: {flow_cfg.type}")

    config_cls, factory = entry
    assert isinstance(flow_cfg, config_cls)
    return factory(flow_cfg, config)


def create_flows(config: AthosConfig) -> Dict[str, BaseFlow]:
    """Create all flows defined in the configuration."""
    return {name: build_flow(name, config) for name in config.execution_flows}


def build_config(config_path: str) -> AthosConfig:
    """Load configuration from disk and apply logging configuration."""
    config = ConfigLoader.load_config(config_path)
    workspace = get_workspace(config)
    try:
        object.__setattr__(config, "workspace_path", workspace)
    except Exception:
        pass
    if config.logging_config is not None:
        configure_logging(config.logging_config)
    return config
