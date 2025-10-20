"""Base flow interface definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput


class BaseFlow(ABC):
    """Enhanced base interface for all flow implementations."""

    # Class-level metadata populated by concrete flows
    name: str = "base_flow"
    description: str = "Base flow"
    supported_modes: list[ExecutionMode] = [ExecutionMode.SYNC]

    @abstractmethod
    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute the flow once and return structured output."""
        raise NotImplementedError

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream execution with intermediate updates."""
        result = await self.execute(input)
        yield result

    async def initialize(self, config: Any) -> None:
        """Perform one-time initialization for expensive resources."""
        return None

    async def cleanup(self) -> None:
        """Release any resources held by the flow instance."""
        return None

    def can_stream(self) -> bool:
        """Return whether this flow advertises streaming support."""
        return ExecutionMode.STREAMING in self.supported_modes
