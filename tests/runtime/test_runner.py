"""Tests for the FlowRunner orchestration component."""

from __future__ import annotations

from pathlib import Path

import pytest

from athos.config.models import AthosConfig, BaseFlowConfig, ModelConfig, ToolFramework
from athos.interfaces.base_flow import BaseFlow
from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
from athos.registry.flow_registry import (
    FLOW_REGISTRY,
    FlowRegistration,
    register_flow,
)
from athos.runtime.runner import FlowRunner
from athos.runtime.session_store import InMemorySessionStore

TEST_FLOW_TYPE = "test.echo"


class EchoFlowConfig(BaseFlowConfig):
    """Configuration used for the tracking echo flow."""

    type: str = TEST_FLOW_TYPE
    response_text: str = "Echo"
    should_fail: bool = False


class TrackingEchoFlow(BaseFlow):
    """Simple flow that records lifecycle interactions for assertions."""

    name = "tracking_echo"
    supported_modes = [ExecutionMode.SYNC]

    initialize_calls = 0
    cleanup_calls = 0
    instances_created = 0

    def __init__(self, config: EchoFlowConfig) -> None:
        self._config = config
        self._initialized = False
        TrackingEchoFlow.instances_created += 1

    @classmethod
    async def create(cls, flow_config, athos_config):
        """Create method - not used in legacy pattern."""
        raise NotImplementedError("Legacy flow uses factory function")

    @classmethod
    def reset_counters(cls) -> None:
        cls.initialize_calls = 0
        cls.cleanup_calls = 0
        cls.instances_created = 0

    async def initialize(self, config: EchoFlowConfig) -> None:  # type: ignore[override]
        self._initialized = True
        TrackingEchoFlow.initialize_calls += 1

    async def execute(self, input: FlowInput) -> FlowOutput:  # type: ignore[override]
        if not self._initialized:
            raise RuntimeError("Flow must be initialized before execution")
        if self._config.should_fail:
            raise RuntimeError("Flow failure triggered")
        return FlowOutput(content=f"{self._config.response_text}: {input.message}")

    async def cleanup(self) -> None:  # type: ignore[override]
        TrackingEchoFlow.cleanup_calls += 1


async def _create_runner(
    tmp_path: Path,
    *,
    should_fail: bool = False,
) -> FlowRunner:
    """Helper to construct a FlowRunner bound to a temporary workspace."""

    config = AthosConfig(
        workspace_dir=str(tmp_path),
        models={
            "model-test": ModelConfig(model_id="model-test"),
        },
        flows={
            "test-flow": {
                "type": TEST_FLOW_TYPE,
                "model": "model-test",
                "response_text": "Response",
                "should_fail": should_fail,
            }
        },
    )
    object.__setattr__(config, "workspace_path", tmp_path)
    return FlowRunner(config, session_store=InMemorySessionStore())


def _ensure_flow_registered() -> None:
    if TEST_FLOW_TYPE not in FLOW_REGISTRY:
        register_flow(
            TEST_FLOW_TYPE,
            EchoFlowConfig,
            lambda cfg, _config: TrackingEchoFlow(cfg),
            framework=ToolFramework.SMOLAGENTS,
        )


@pytest.fixture(autouse=True)
def register_test_flow() -> None:
    TrackingEchoFlow.reset_counters()
    _ensure_flow_registered()
    # Reset registry entry to use fresh factory for each test run
    FLOW_REGISTRY[TEST_FLOW_TYPE] = FlowRegistration(
        config_cls=EchoFlowConfig,
        creator=lambda cfg, _config: TrackingEchoFlow(cfg),
        framework=ToolFramework.SMOLAGENTS,
    )


@pytest.mark.asyncio
async def test_execute_success(tmp_path: Path) -> None:
    runner = await _create_runner(tmp_path)

    result = await runner.execute(
        flow_name="test-flow",
        message="hello",
        session_id="session-1",
        user_id="user-1",
    )

    assert result.success is True
    assert result.output is not None
    assert result.output.content == "Response: hello"
    session = await runner.session_store.get_or_create("session-1", "user-1")
    assert session.get_history() == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Response: hello"},
    ]


@pytest.mark.asyncio
async def test_execute_handles_flow_error(tmp_path: Path) -> None:
    runner = await _create_runner(tmp_path, should_fail=True)

    result = await runner.execute(
        flow_name="test-flow",
        message="boom",
        session_id="session-2",
        user_id="user-1",
    )

    assert result.success is False
    assert result.error == "Flow failure triggered"
    session = await runner.session_store.get_or_create("session-2", "user-1")
    assert session.get_history() == []


@pytest.mark.asyncio
async def test_session_reuse(tmp_path: Path) -> None:
    runner = await _create_runner(tmp_path)

    await runner.execute(
        flow_name="test-flow",
        message="first",
        session_id="shared",
        user_id="user-1",
    )
    await runner.execute(
        flow_name="test-flow",
        message="second",
        session_id="shared",
        user_id="user-1",
    )

    session = await runner.session_store.get_or_create("shared", "user-1")
    assert [msg["content"] for msg in session.get_history()] == [
        "first",
        "Response: first",
        "second",
        "Response: second",
    ]


@pytest.mark.asyncio
async def test_flow_caching(tmp_path: Path) -> None:
    runner = await _create_runner(tmp_path)

    await runner.execute("test-flow", "one", "session", "user-1")
    await runner.execute("test-flow", "two", "session", "user-1")

    assert TrackingEchoFlow.instances_created == 1
    assert TrackingEchoFlow.initialize_calls == 1


@pytest.mark.asyncio
async def test_cleanup_invokes_flow_cleanup(tmp_path: Path) -> None:
    runner = await _create_runner(tmp_path)

    await runner.execute("test-flow", "one", "session", "user-1")
    await runner.cleanup()

    assert TrackingEchoFlow.cleanup_calls == 1
    assert runner._flow_cache == {}
