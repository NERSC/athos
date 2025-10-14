"""Core runtime primitives for Athos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_flow import BaseFlow

if TYPE_CHECKING:
    from athos.config import AthosConfig

__all__ = ["BaseFlow", "build_config", "build_flow", "create_flows"]


def build_flow(flow_name: str, config: "AthosConfig") -> BaseFlow:
    """Construct a flow instance using the runtime helpers."""

    from .runtime import build_flow as _build_flow

    return _build_flow(flow_name, config)


def create_flows(config: "AthosConfig") -> Dict[str, BaseFlow]:
    """Create all flows defined in the given configuration."""

    from .runtime import create_flows as _create_flows

    return _create_flows(config)


def build_config(
    config_path: str, overrides: Optional[Dict[str, Any]] = None
) -> "AthosConfig":
    """Load configuration data via the runtime helpers."""

    from .runtime import build_config as _build_config

    return _build_config(config_path, overrides)
