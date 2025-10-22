"""Compatibility helpers for adapting legacy flow interfaces."""

from __future__ import annotations

import inspect
import logging
from typing import Any

from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput

logger = logging.getLogger(__name__)


class LegacyFlowAdapter(BaseFlow):
    """Adapter that allows legacy flows to run within the new runtime."""

    def __init__(self, legacy_flow: BaseFlow) -> None:
        self._legacy_flow = legacy_flow

        # Mirror metadata when available so downstream code keeps working.
        self.name = getattr(legacy_flow, "name", legacy_flow.__class__.__name__)
        self.description = getattr(legacy_flow, "description", "")
        legacy_modes = getattr(legacy_flow, "supported_modes", self.supported_modes)
        self.supported_modes = list(legacy_modes)

    @classmethod
    async def create(cls, flow_config: Any, athos_config: Any):
        """Create method - not used for adapters (they wrap existing flows)."""
        raise NotImplementedError("LegacyFlowAdapter wraps existing flows, use constructor instead")

    async def execute(self, input: FlowInput) -> FlowOutput:  # type: ignore[override]
        """Invoke the legacy ``execute`` method and wrap its result."""

        legacy_execute = getattr(self._legacy_flow, "execute", None)
        if legacy_execute is None:
            raise AttributeError(
                f"Legacy flow {self._legacy_flow!r} has no execute method"
            )

        result = legacy_execute(input.message)
        if inspect.isawaitable(result):
            result = await result

        if isinstance(result, FlowOutput):
            return result

        if result is None:
            logger.warning(
                "Legacy flow '%s' returned None; converting to empty FlowOutput",
                self.name,
            )
            content = ""
        else:
            content = str(result)

        return FlowOutput(content=content)

    async def initialize(self, config: Any) -> None:  # type: ignore[override]
        """Forward initialization to the legacy flow when supported."""

        initializer = getattr(self._legacy_flow, "initialize", None)
        if initializer is None:
            return

        result = initializer(config)
        if inspect.isawaitable(result):
            await result

    async def cleanup(self) -> None:  # type: ignore[override]
        """Delegate to ``cleanup``/``close`` on the legacy flow when available."""

        for attr in ("close", "cleanup"):
            hook = getattr(self._legacy_flow, attr, None)
            if hook is None:
                continue
            result = hook()
            if inspect.isawaitable(result):
                await result
            break


def is_new_interface(flow: BaseFlow) -> bool:
    """Return ``True`` when a flow's execute method consumes ``FlowInput``."""

    execute = getattr(flow, "execute", None)
    if execute is None:
        return False

    try:
        params = list(inspect.signature(execute).parameters.values())
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return False

    if len(params) != 1:
        return False

    annotation = params[0].annotation
    if annotation is FlowInput:
        return True

    if annotation is inspect.Signature.empty:
        return False

    return "FlowInput" in str(annotation)


__all__ = ["LegacyFlowAdapter", "is_new_interface"]
