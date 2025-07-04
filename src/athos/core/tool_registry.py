from typing import Callable, Dict
from importlib.metadata import entry_points
import logging

from smolagents import Tool
from athos.config import ToolConfig

logger = logging.getLogger(__name__)

ToolFactory = Callable[[ToolConfig], Tool]
TOOL_REGISTRY: Dict[str, ToolFactory] = {}


def register_tool(tool_name: str, factory: ToolFactory) -> None:
    """Register a new tool factory."""
    TOOL_REGISTRY[tool_name] = factory


def load_plugins() -> None:
    """Load tool plugins from entry points."""
    try:
        eps = entry_points(group="athos_tools")
        iterable = list(eps)
    except Exception:
        logger.warning("Failed to read tool entry points; skipping plugin load")
        return
    for ep in iterable:
        try:
            logger.info("Loading tool plugin %s", ep.name)
            plugin = ep.load()
            plugin()
        except Exception as exc:
            logger.warning("Failed to load tool plugin %s: %s", ep.name, exc)

