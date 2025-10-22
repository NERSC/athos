"""Base flow interface definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, ClassVar, Type
from typing_extensions import Self

from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput


class BaseFlow(ABC):
    """Enhanced base interface for all flow implementations.

    New Pattern (Recommended):
    ---------------------------
    Flows should implement the create() classmethod to build all dependencies
    and call the constructor with fully-initialized objects. This eliminates
    uninitialized state and provides better type safety.

    Example:
        class MyFlow(BaseFlow):
            name = "my_flow"
            description = "My flow description"
            config_class = MyFlowConfig
            framework = ToolFramework.LANGGRAPH
            supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

            def __init__(self, model: BaseLanguageModel, config: AthosConfig):
                self.model = model  # Required, not Optional
                self.config = config

            @classmethod
            async def create(
                cls,
                flow_config: MyFlowConfig,
                athos_config: AthosConfig
            ) -> Self:
                model = build_model(athos_config.models[flow_config.model])
                return cls(model=model, config=athos_config)

            async def execute(self, input: FlowInput) -> FlowOutput:
                # Use self.model safely without None checks
                response = await self.model.generate(input.message)
                return FlowOutput(content=response)

    Legacy Pattern (Deprecated):
    ----------------------------
    The old pattern used factory functions and initialize() method.
    This is still supported but will be removed in a future version.
    """

    # ===== Class-level metadata (required for new pattern) =====
    name: ClassVar[str]
    """Unique flow identifier used in registry and config"""

    description: ClassVar[str] = ""
    """Human-readable description of what this flow does"""

    config_class: ClassVar[Type[Any]]
    """Pydantic config class for this flow's configuration"""

    framework: ClassVar[Any]
    """Framework this flow uses (SMOLAGENTS, LANGGRAPH, etc.)"""

    supported_modes: ClassVar[list[ExecutionMode]] = [ExecutionMode.SYNC]
    """Execution modes this flow supports"""

    # ===== Primary construction method (NEW PATTERN) =====
    @classmethod
    @abstractmethod
    async def create(
        cls,
        flow_config: Any,
        athos_config: Any
    ) -> Self:
        """Create and fully initialize a flow instance.

        This is the primary way to construct flows in production.
        Subclasses must:
        1. Build all dependencies (models, tools, MCP clients)
        2. Call constructor with all required arguments
        3. Return a fully-initialized, ready-to-use flow

        Args:
            flow_config: Flow-specific configuration
            athos_config: Full ATHOS configuration

        Returns:
            Fully initialized flow instance

        Raises:
            ValueError: If configuration is invalid or dependencies missing
        """
        raise NotImplementedError(
            f"{cls.__name__} must implement create() classmethod"
        )

    # ===== Core execution interface =====
    @abstractmethod
    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute the flow once and return structured output.

        Args:
            input: FlowInput containing message, session, mode, metadata

        Returns:
            FlowOutput with content, artifacts, metadata
        """
        raise NotImplementedError

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream execution with intermediate updates.

        Default implementation falls back to execute().
        Override for true streaming support.

        Args:
            input: FlowInput containing message, session, mode, metadata

        Yields:
            FlowOutput chunks (intermediate and final)
        """
        result = await self.execute(input)
        yield result

    # ===== Lifecycle management =====
    async def initialize(self, config: Any) -> None:
        """[DEPRECATED] One-time initialization for expensive resources.

        This method is deprecated in favor of the create() classmethod.
        New flows should not implement this - all setup should happen
        in create() before calling the constructor.

        Will be removed in a future version.
        """
        pass  # Default no-op for new flows

    async def cleanup(self) -> None:
        """Release any resources held by the flow instance.

        Called by FlowRunner during shutdown. Override if your flow
        manages resources like MCP connections, file handles, etc.
        """
        pass

    # ===== Capability detection =====
    def can_stream(self) -> bool:
        """Return whether this flow supports streaming execution."""
        return ExecutionMode.STREAMING in self.supported_modes
