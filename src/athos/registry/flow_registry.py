from dataclasses import dataclass
from typing import Dict, Optional, Type

from athos.interfaces.base_flow import BaseFlow
from athos.config.models import BaseFlowConfig, ToolFramework

# ===== Type definitions =====
FlowClass = Type[BaseFlow]


@dataclass(frozen=True)
class FlowRegistration:
    """Metadata stored for each registered flow type."""

    config_cls: Type[BaseFlowConfig]
    creator: FlowClass
    framework: ToolFramework


FLOW_REGISTRY: Dict[str, FlowRegistration] = {}


def register_flow(flow_class: FlowClass) -> None:
    """Register a flow type with the runtime.

    Usage:
        @register_flow_type
        class MyFlow(BaseFlow):
            name = "my_flow"
            config_class = MyFlowConfig
            framework = ToolFramework.LANGGRAPH
            ...

        # Or without decorator:
        register_flow(MyFlow)

    Args:
        flow_class: A BaseFlow subclass with required class metadata

    Raises:
        ValueError: If class metadata is missing or invalid
        TypeError: If argument is not a BaseFlow subclass
    """

    if not (isinstance(flow_class, type) and issubclass(flow_class, BaseFlow)):
        raise TypeError(
            f"Argument must be a BaseFlow subclass, got {type(flow_class)}"
        )

    # Validate required class metadata
    missing = []
    if not hasattr(flow_class, 'name') or not flow_class.name:
        missing.append('name')
    if not hasattr(flow_class, 'config_class') or not flow_class.config_class:
        missing.append('config_class')
    if not hasattr(flow_class, 'framework') or not flow_class.framework:
        missing.append('framework')

    if missing:
        raise ValueError(
            f"{flow_class.__name__} missing required class attributes: {', '.join(missing)}\n"
            f"Flows must define: name, config_class, framework"
        )

    # Validate create() method exists
    if not hasattr(flow_class, 'create'):
        raise ValueError(
            f"{flow_class.__name__} missing create() classmethod.\n"
            f"Flows must implement: @classmethod async def create(...)"
        )

    FLOW_REGISTRY[flow_class.name] = FlowRegistration(
        config_cls=flow_class.config_class,
        creator=flow_class,
        framework=flow_class.framework,
    )


def register_flow_type(flow_class: FlowClass) -> FlowClass:
    """Decorator to auto-register a flow class.

    Usage:
        @register_flow_type
        class MyFlow(BaseFlow):
            name = "my_flow"
            config_class = MyFlowConfig
            framework = ToolFramework.LANGGRAPH
            ...

    The decorator returns the class unchanged, so it can be imported normally.
    """
    register_flow(flow_class)
    return flow_class


def get_available_flow_types() -> Dict[str, Type[BaseFlowConfig]]:
    """Get all available flow types and their config classes."""
    return {
        flow_type: registration.config_cls
        for flow_type, registration in FLOW_REGISTRY.items()
    }


def is_flow_type_registered(flow_type: str) -> bool:
    """Check if a flow type is registered."""
    return flow_type in FLOW_REGISTRY


def get_flow_registration(flow_type: str) -> Optional[FlowRegistration]:
    """Get registration metadata for a flow type.

    Args:
        flow_type: The flow type name

    Returns:
        FlowRegistration if found, None otherwise
    """
    return FLOW_REGISTRY.get(flow_type)
