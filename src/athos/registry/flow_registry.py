from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type, Union, overload

from athos.interfaces.base_flow import BaseFlow
from athos.config.models import BaseFlowConfig, AthosConfig, ToolFramework

# ===== Type definitions =====
# Old pattern: standalone factory function
FlowFactory = Callable[[BaseFlowConfig, AthosConfig], BaseFlow]

# New pattern: flow class with create() classmethod
FlowClass = Type[BaseFlow]

# Union of both patterns
FlowCreator = Union[FlowFactory, FlowClass]


@dataclass(frozen=True)
class FlowRegistration:
    """Metadata stored for each registered flow type."""

    config_cls: Type[BaseFlowConfig]
    creator: FlowCreator  # Can be factory function OR flow class
    framework: ToolFramework


FLOW_REGISTRY: Dict[str, FlowRegistration] = {}


# ===== Registration function with overloads =====
@overload
def register_flow(flow_class: FlowClass) -> None:
    """Register a flow using class metadata (new pattern)."""
    ...


@overload
def register_flow(
    flow_type: str,
    config_cls: Type[BaseFlowConfig],
    creator: FlowCreator,
    *,
    framework: ToolFramework,
) -> None:
    """Register a flow with explicit arguments (legacy pattern)."""
    ...


def register_flow(
    flow_class_or_type: Union[FlowClass, str],
    config_cls: Optional[Type[BaseFlowConfig]] = None,
    creator: Optional[FlowCreator] = None,
    *,
    framework: Optional[ToolFramework] = None,
) -> None:
    """Register a flow type with the runtime.

    Supports two patterns:

    NEW PATTERN (recommended):
        @register_flow_type
        class MyFlow(BaseFlow):
            name = "my_flow"
            config_class = MyFlowConfig
            framework = ToolFramework.LANGGRAPH
            ...

        # Or without decorator:
        register_flow(MyFlow)

    LEGACY PATTERN (deprecated):
        register_flow(
            "my_flow",
            MyFlowConfig,
            create_my_flow_factory,
            framework=ToolFramework.LANGGRAPH
        )

    Args:
        flow_class_or_type: Either a BaseFlow subclass (new pattern) or
            flow type string (legacy pattern)
        config_cls: Flow config class (legacy pattern only)
        creator: Factory function or flow class (legacy pattern only)
        framework: Framework enum (legacy pattern only)

    Raises:
        ValueError: If class metadata is missing or invalid
        TypeError: If arguments don't match either pattern
    """

    # ===== NEW PATTERN: Single class argument =====
    if isinstance(flow_class_or_type, type) and issubclass(flow_class_or_type, BaseFlow):
        flow_class = flow_class_or_type

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
                f"New pattern flows must define: name, config_class, framework"
            )

        # Validate create() method exists
        if not hasattr(flow_class, 'create'):
            raise ValueError(
                f"{flow_class.__name__} missing create() classmethod.\n"
                f"New pattern flows must implement: @classmethod async def create(...)"
            )

        FLOW_REGISTRY[flow_class.name] = FlowRegistration(
            config_cls=flow_class.config_class,
            creator=flow_class,
            framework=flow_class.framework,
        )
        return

    # ===== LEGACY PATTERN: Multiple arguments =====
    if not isinstance(flow_class_or_type, str):
        raise TypeError(
            f"First argument must be a BaseFlow subclass or flow type string, "
            f"got {type(flow_class_or_type)}"
        )

    if config_cls is None or creator is None or framework is None:
        raise ValueError(
            "Legacy pattern requires all arguments: "
            "register_flow(flow_type, config_cls, creator, framework=...)"
        )

    flow_type = flow_class_or_type
    FLOW_REGISTRY[flow_type] = FlowRegistration(
        config_cls=config_cls,
        creator=creator,
        framework=framework,
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
