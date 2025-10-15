from typing import Callable, Dict, Tuple, Type

from athos.interfaces.base_flow import BaseFlow
from athos.config.models import BaseFlowConfig

from athos.config.models import AthosConfig

FlowFactory = Callable[[BaseFlowConfig, AthosConfig], BaseFlow]
FLOW_REGISTRY: Dict[str, Tuple[Type[BaseFlowConfig], FlowFactory]] = {}


def register_flow(flow_type: str, config_cls: Type[BaseFlowConfig], factory: FlowFactory) -> None:
    """Register a new flow type."""
    FLOW_REGISTRY[flow_type] = (config_cls, factory)


def get_available_flow_types() -> Dict[str, Type[BaseFlowConfig]]:
    """Get all available flow types and their config classes."""
    return {flow_type: config_cls for flow_type, (config_cls, _) in FLOW_REGISTRY.items()}


def is_flow_type_registered(flow_type: str) -> bool:
    """Check if a flow type is registered."""
    return flow_type in FLOW_REGISTRY
