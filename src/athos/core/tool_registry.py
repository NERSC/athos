from typing import Callable, Dict

from smolagents import Tool
from athos.config import ToolConfig

ToolFactory = Callable[[ToolConfig], Tool]
TOOL_REGISTRY: Dict[str, ToolFactory] = {}


def register_tool(tool_name: str, factory: ToolFactory) -> None:
    """Register a new tool factory."""
    TOOL_REGISTRY[tool_name] = factory

