"""Tests for the legacy compatibility adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from athos.config.models import AthosConfig, BaseFlowConfig, ModelConfig, ToolFramework
from athos.interfaces.base_flow import BaseFlow
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
from athos.models.session import FlowSession
from athos.registry.flow_registry import FLOW_REGISTRY, FlowRegistration, register_flow
from athos.runtime.compat import LegacyFlowAdapter, is_new_interface
from athos.runtime.runner import FlowRunner
from athos.runtime.session_store import InMemorySessionStore


class LegacyEchoFlow(BaseFlow):
    """Simple legacy-style flow returning a string response."""

    name = "legacy_echo"
    description = "Legacy echo flow for tests"

    def __init__(self) -> None:
        self.last_message: str | None = None
        self.cleaned = False
        self.initialized_with: Any | None = None

    async def initialize(self, config: Any) -> None:  # type: ignore[override]
        self.initialized_with = config

    async def execute(self, message: str) -> str:  # type: ignore[override]
        self.last_message = message
        return f"echo:{message}"

    async def close(self) -> None:
        self.cleaned = True


class LegacyFlowOutputFlow(BaseFlow):
    """Legacy flow that already returns a ``FlowOutput`` instance."""

    async def execute(self, message: str) -> FlowOutput:  # type: ignore[override]
        return FlowOutput(content=message.upper(), metadata={"legacy": True})


@pytest.mark.asyncio
async def test_adapter_wraps_legacy_flow(tmp_path: Path) -> None:
    session = FlowSession(
        session_id="s-1",
        user_id="user",
        workspace=tmp_path,
    )
    flow_input = FlowInput(
        message="hello",
        session=session,
        mode=ExecutionMode.SYNC,
    )

    legacy = LegacyEchoFlow()
    adapter = LegacyFlowAdapter(legacy)

    output = await adapter.execute(flow_input)

    assert output.content == "echo:hello"
    assert legacy.last_message == "hello"

    await adapter.cleanup()
    assert legacy.cleaned is True


@pytest.mark.asyncio
async def test_adapter_preserves_flow_output(tmp_path: Path) -> None:
    session = FlowSession(
        session_id="s-2",
        user_id="user",
        workspace=tmp_path,
    )
    flow_input = FlowInput(
        message="legacy",
        session=session,
        mode=ExecutionMode.SYNC,
    )

    legacy = LegacyFlowOutputFlow()
    adapter = LegacyFlowAdapter(legacy)

    output = await adapter.execute(flow_input)

    assert output.content == "LEGACY"
    assert output.metadata == {"legacy": True}


def test_is_new_interface_detection() -> None:
    class NewStyleFlow(BaseFlow):
        async def execute(self, input: FlowInput) -> FlowOutput:  # type: ignore[override]
            return FlowOutput(content=input.message)

    assert is_new_interface(NewStyleFlow()) is True
    assert is_new_interface(LegacyEchoFlow()) is False


@pytest.mark.asyncio
async def test_runner_adapts_legacy_flows(tmp_path: Path) -> None:
    flow_type = "tests.legacy.echo"

    class LegacyConfig(BaseFlowConfig):
        type: str = flow_type

    def factory(cfg: LegacyConfig, _config: AthosConfig) -> BaseFlow:
        return LegacyEchoFlow()

    register_flow(
        flow_type,
        LegacyConfig,
        factory,
        framework=ToolFramework.SMOLAGENTS,
    )
    # Ensure registry entry is reset for the duration of the test.
    FLOW_REGISTRY[flow_type] = FlowRegistration(
        config_cls=LegacyConfig,
        factory=factory,
        framework=ToolFramework.SMOLAGENTS,
    )

    config = AthosConfig(
        workspace_dir=str(tmp_path),
        models={"model": ModelConfig(model_id="model")},
        flows={
            "legacy-flow": {
                "type": flow_type,
                "model": "model",
            }
        },
    )
    object.__setattr__(config, "workspace_path", tmp_path)

    runner = FlowRunner(config, session_store=InMemorySessionStore())

    result = await runner.execute(
        flow_name="legacy-flow",
        message="ping",
        session_id="session",
        user_id="user",
    )

    assert result.success is True
    assert result.output is not None
    assert result.output.content == "echo:ping"

    session = await runner.session_store.get_or_create("session", "user")
    assert session.get_history()[-2:] == [
        {"role": "user", "content": "ping"},
        {"role": "assistant", "content": "echo:ping"},
    ]
