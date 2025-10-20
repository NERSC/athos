from dataclasses import dataclass
from typing import Callable, Dict, Type

from athos.interfaces.base_flow import BaseFlow
from athos.config.models import BaseFlowConfig, AthosConfig, ToolFramework

FlowFactory = Callable[[BaseFlowConfig, AthosConfig], BaseFlow]


@dataclass(frozen=True)
class FlowRegistration:
    """Metadata stored for each registered flow type."""

    config_cls: Type[BaseFlowConfig]
    factory: FlowFactory
    framework: ToolFramework


FLOW_REGISTRY: Dict[str, FlowRegistration] = {}


def register_flow(
    flow_type: str,
    config_cls: Type[BaseFlowConfig],
    factory: FlowFactory,
    *,
    framework: ToolFramework,
) -> None:
    """Register a new flow type."""
    FLOW_REGISTRY[flow_type] = FlowRegistration(
        config_cls=config_cls,
        factory=factory,
        framework=framework,
    )


def get_available_flow_types() -> Dict[str, Type[BaseFlowConfig]]:
    """Get all available flow types and their config classes."""
    return {
        flow_type: registration.config_cls
        for flow_type, registration in FLOW_REGISTRY.items()
    }


def is_flow_type_registered(flow_type: str) -> bool:
    """Check if a flow type is registered."""
    return flow_type in FLOW_REGISTRY
