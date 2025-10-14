from abc import ABC, abstractmethod
from typing import Any


class BaseFlow(ABC):
    """Base class for all flows."""

    @abstractmethod
    async def execute(self, input_data: str) -> Any:
        """Execute the flow with input data."""
        raise NotImplementedError

    def close(self) -> None:
        """Clean up any resources held by the flow."""
        # Most flows do not need explicit cleanup, so provide a no-op default.
        return None
