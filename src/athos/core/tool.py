from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

T = TypeVar('T')

class Tool(ABC, Generic[T]):
    name: str
    description: str
    inputs: Dict[str, Any]  # e.g., input name → type/description schema
    output_type: Any        # e.g., pydantic-type descriptor

    @abstractmethod
    def forward(self, **kwargs) -> T:
        raise NotImplementedError("Subclasses must implement the forward method")