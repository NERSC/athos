from typing import Callable, Dict, Tuple, Type
from importlib.metadata import entry_points
import logging

from athos.core.flows import BaseFlow
from athos.config.models import BaseFlowConfig

logger = logging.getLogger(__name__)

FlowFactory = Callable[[BaseFlowConfig, "AthosManager"], BaseFlow]
FLOW_REGISTRY: Dict[str, Tuple[Type[BaseFlowConfig], FlowFactory]] = {}


def register_flow(flow_type: str, config_cls: Type[BaseFlowConfig], factory: FlowFactory) -> None:
    """Register a new flow type."""
    FLOW_REGISTRY[flow_type] = (config_cls, factory)


def load_plugins() -> None:
    """Load flow plugins from entry points."""
    try:
        eps = entry_points(group="athos_flows")
        iterable = list(eps)
    except Exception:
        logger.warning("Failed to read entry points; skipping plugin load")
        return

    for ep in iterable:
        try:
            logger.info("Loading flow plugin %s", ep.name)
            plugin = ep.load()
            # Call the plugin function to register the flow
            plugin()
            logger.info("Successfully loaded flow plugin %s", ep.name)
        except Exception as exc:
            logger.warning("Failed to load flow plugin %s: %s", ep.name, exc)


def get_available_flow_types() -> Dict[str, Type[BaseFlowConfig]]:
    """Get all available flow types and their config classes."""
    return {flow_type: config_cls for flow_type, (config_cls, _) in FLOW_REGISTRY.items()}


def is_flow_type_registered(flow_type: str) -> bool:
    """Check if a flow type is registered."""
    return flow_type in FLOW_REGISTRY
