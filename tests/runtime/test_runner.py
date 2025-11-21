"""Tests for the FlowRunner orchestration component."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator

import pytest
from langchain_core.messages import AIMessage, HumanMessage

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
STREAM_FLOW_TYPE = "test.streaming"


class EchoFlowConfig(BaseFlowConfig):
    """Configuration used for the tracking echo flow."""

    type: str = TEST_FLOW_TYPE
    response_text: str = "Echo"
    should_fail: bool = False


class TrackingEchoFlow(BaseFlow):
    """Simple flow that records lifecycle interactions for assertions."""

    name = TEST_FLOW_TYPE
    config_class = EchoFlowConfig
    framework = ToolFramework.SMOLAGENTS
    supported_modes = [ExecutionMode.SYNC]

    cleanup_calls = 0
    instances_created = 0

    def __init__(self, config: EchoFlowConfig) -> None:
        self._config = config
        TrackingEchoFlow.instances_created += 1

    @classmethod
    async def create(cls, flow_config: EchoFlowConfig, athos_config: AthosConfig):
        """Create and return fully initialized flow."""
        return cls(flow_config)

    @classmethod
    def reset_counters(cls) -> None:
        cls.cleanup_calls = 0
        cls.instances_created = 0

    async def execute(self, input: FlowInput) -> FlowOutput:  # type: ignore[override]
        if self._config.should_fail:
            raise RuntimeError("Flow failure triggered")
        return FlowOutput(content=f"{self._config.response_text}: {input.message}")

    async def cleanup(self) -> None:  # type: ignore[override]
        TrackingEchoFlow.cleanup_calls += 1


class StreamingFlowConfig(BaseFlowConfig):
    """Configuration for the incremental streaming test flow."""

    type: str = STREAM_FLOW_TYPE
    model: str = "stream-model"
    parts: list[str] = ["chunk"]
    fail_after_chunks: int | None = None


class IncrementalStreamingFlow(BaseFlow):
    """Flow that emits only incremental streaming deltas for testing."""

    name = STREAM_FLOW_TYPE
    config_class = StreamingFlowConfig
    framework = ToolFramework.SMOLAGENTS
    supported_modes = [ExecutionMode.STREAMING]

    def __init__(self, config: StreamingFlowConfig) -> None:
        self._config = config

    @classmethod
    async def create(
        cls, flow_config: StreamingFlowConfig, athos_config: AthosConfig
    ) -> "IncrementalStreamingFlow":
        return cls(flow_config)

    async def execute(self, input: FlowInput) -> FlowOutput:  # type: ignore[override]
        return FlowOutput(content="".join(self._config.parts))

    async def stream(
        self, input: FlowInput
    ) -> AsyncGenerator[FlowOutput, None]:  # type: ignore[override]
        for idx, part in enumerate(self._config.parts):
            if (
                self._config.fail_after_chunks is not None
                and idx == self._config.fail_after_chunks
            ):
                raise RuntimeError("Stream failure triggered")
            yield FlowOutput(
                content=part,
                metadata={"streaming": True, "chunk": True},
            )
        yield FlowOutput(
            content="",
            metadata={"streaming": True, "final": True},
        )


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
        register_flow(TrackingEchoFlow)
    if STREAM_FLOW_TYPE not in FLOW_REGISTRY:
        register_flow(IncrementalStreamingFlow)


@pytest.fixture(autouse=True)
def register_test_flow() -> None:
    TrackingEchoFlow.reset_counters()
    _ensure_flow_registered()
    # Reset registry entry
    FLOW_REGISTRY[TEST_FLOW_TYPE] = FlowRegistration(
        config_cls=EchoFlowConfig,
        creator=TrackingEchoFlow,
        framework=ToolFramework.SMOLAGENTS,
    )
    FLOW_REGISTRY[STREAM_FLOW_TYPE] = FlowRegistration(
        config_cls=StreamingFlowConfig,
        creator=IncrementalStreamingFlow,
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
    history = session.get_history()
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert history[0].content == "hello"
    assert isinstance(history[1], AIMessage)
    assert history[1].content == "Response: hello"


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
    history = session.get_history()
    assert [msg.content for msg in history] == [
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


@pytest.mark.asyncio
async def test_cleanup_invokes_flow_cleanup(tmp_path: Path) -> None:
    runner = await _create_runner(tmp_path)

    await runner.execute("test-flow", "one", "session", "user-1")
    await runner.cleanup()

    assert TrackingEchoFlow.cleanup_calls == 1
    assert runner._flow_cache == {}


@pytest.mark.asyncio
async def test_streaming_flow_records_incremental_history(tmp_path: Path) -> None:
    config = AthosConfig(
        workspace_dir=str(tmp_path),
        models={"stream-model": ModelConfig(model_id="stream-model")},
        flows={
            "stream-flow": {
                "type": STREAM_FLOW_TYPE,
                "parts": ["Hel", "lo"],
            }
        },
    )
    object.__setattr__(config, "workspace_path", tmp_path)

    runner = FlowRunner(config, session_store=InMemorySessionStore())

    chunks = []
    async for output in runner.stream(
        flow_name="stream-flow",
        message="hello",
        session_id="stream-session",
        user_id="stream-user",
    ):
        chunks.append(output)

    assert [chunk.content for chunk in chunks] == ["Hel", "lo", ""]
    assert chunks[-1].metadata.get("final") is True

    session = await runner.session_store.get_or_create("stream-session", "stream-user")
    history = session.get_history()
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert history[0].content == "hello"
    assert isinstance(history[1], AIMessage)
    assert history[1].content == "Hello"


@pytest.mark.asyncio
async def test_streaming_flow_records_partial_history_on_error(tmp_path: Path) -> None:
    config = AthosConfig(
        workspace_dir=str(tmp_path),
        models={"stream-model": ModelConfig(model_id="stream-model")},
        flows={
            "stream-fail": {
                "type": STREAM_FLOW_TYPE,
                "parts": ["Hi", " there"],
                "fail_after_chunks": 1,
            }
        },
    )
    object.__setattr__(config, "workspace_path", tmp_path)

    runner = FlowRunner(config, session_store=InMemorySessionStore())

    stream = runner.stream(
        flow_name="stream-fail",
        message="uh oh",
        session_id="fail-session",
        user_id="stream-user",
    )

    first_chunk = await anext(stream)
    assert first_chunk.content == "Hi"

    with pytest.raises(RuntimeError, match="Stream failure triggered"):
        await anext(stream)

    session = await runner.session_store.get_or_create("fail-session", "stream-user")
    history = session.get_history()
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert history[0].content == "uh oh"
    assert isinstance(history[1], AIMessage)
    assert history[1].content == "Hi"
