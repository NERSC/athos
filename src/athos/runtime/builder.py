"""Runtime helpers to construct and execute flows without a manager."""

from typing import Any, Dict, Optional
import asyncio
import logging
import inspect

from athos.config import AthosConfig, ConfigLoader
from athos.interfaces.base_flow import BaseFlow
from athos.registry.flow_registry import FLOW_REGISTRY
from athos.utils.logging_utils import configure_logging
from athos.utils.workspace import get_workspace

logger = logging.getLogger(__name__)


async def build_flow(flow_name: str, config: AthosConfig) -> BaseFlow:
    """Construct a flow instance using its create() classmethod.

    Args:
        flow_name: Name of the flow from config.flows
        config: Full ATHOS configuration

    Returns:
        Fully initialized flow instance

    Raises:
        ValueError: If flow_name not found or flow type not registered
    """
    if flow_name not in config.flows:
        raise ValueError(f"Unknown flow: {flow_name}")

    flow_cfg = config.flows[flow_name]
    registration = FLOW_REGISTRY.get(flow_cfg.type)
    if not registration:
        raise ValueError(f"Unknown flow type: {flow_cfg.type}")

    config_cls = registration.config_cls
    flow_class = registration.creator

    # Validate config type
    if not isinstance(flow_cfg, config_cls):
        raise TypeError(
            f"Flow '{flow_name}' config has type {type(flow_cfg).__name__} "
            f"but expected {config_cls.__name__}"
        )

    # All flows use create() classmethod
    logger.debug("Building flow '%s' using create() classmethod", flow_name)
    flow = await flow_class.create(flow_cfg, config)

    logger.debug("Flow '%s' built and initialized", flow_name)
    return flow


async def create_flows(config: AthosConfig) -> Dict[str, BaseFlow]:
    """Create all flows defined in the configuration.

    Args:
        config: Full ATHOS configuration

    Returns:
        Dictionary mapping flow names to fully initialized flow instances
    """
    flows = {}
    for name in config.flows:
        flows[name] = await build_flow(name, config)
    return flows


def build_config(config_path: str, overrides: Optional[Dict[str, Any]] = None) -> AthosConfig:
    """Load configuration from disk, apply overrides and logging configuration."""
    config = ConfigLoader.load_config(config_path, overrides)
    workspace = get_workspace(config)
    try:
        object.__setattr__(config, "workspace_path", workspace)
    except Exception:
        pass
    if config.logging_config is not None:
        configure_logging(config.logging_config)
    return config
