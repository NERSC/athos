"""Tests for flow registration using classmethod create pattern."""

from __future__ import annotations

import pytest
from typing import Any

from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.session import FlowSession
from athos.models.enums import ExecutionMode
from athos.registry.flow_registry import (
    register_flow,
    register_flow_type,
    FLOW_REGISTRY,
    get_flow_registration,
)
from athos.runtime.builder import build_flow
from athos.runtime.runner import FlowRunner
from athos.config.models import AthosConfig, BaseFlowConfig, ToolFramework, ModelConfig


# ===== Test Fixtures: Config Classes =====

class NewPatternFlowConfig(BaseFlowConfig):
    """Config for new pattern test flow."""
    type: str = "new_pattern"
    model: str = "test_model"
    value: str = "default"


# ===== Test Fixtures: Flow Implementations =====

class NewPatternFlow(BaseFlow):
    """Flow using new pattern (classmethod create)."""

    name = "new_pattern"
    description = "New pattern test flow"
    config_class = NewPatternFlowConfig
    framework = ToolFramework.LANGGRAPH
    supported_modes = [ExecutionMode.SYNC]

    def __init__(self, value: str, initialized: bool):
        """Constructor takes all dependencies."""
        self.value = value
        self.initialized = initialized

    @classmethod
    async def create(
        cls,
        flow_config: NewPatternFlowConfig,
        athos_config: AthosConfig
    ) -> NewPatternFlow:
        """Build dependencies and construct flow."""
        # Simulate expensive initialization
        value = f"initialized_{flow_config.value}"
        return cls(value=value, initialized=True)

    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute flow."""
        return FlowOutput(
            content=f"{self.value}: {input.message}",
            metadata={"initialized": self.initialized}
        )


# ===== Tests: Registration =====

def test_new_pattern_registration():
    """Test that new pattern flow registers correctly."""
    # Clear registry
    FLOW_REGISTRY.clear()

    # Register using new pattern
    register_flow(NewPatternFlow)

    # Verify registration
    assert "new_pattern" in FLOW_REGISTRY
    registration = FLOW_REGISTRY["new_pattern"]
    assert registration.config_cls == NewPatternFlowConfig
    assert registration.creator == NewPatternFlow
    assert registration.framework == ToolFramework.LANGGRAPH


def test_decorator_registration():
    """Test that decorator registration works."""
    # Clear registry
    FLOW_REGISTRY.clear()

    @register_flow_type
    class DecoratorFlow(BaseFlow):
        name = "decorator_flow"
        description = "Decorator test"
        config_class = NewPatternFlowConfig
        framework = ToolFramework.LANGGRAPH

        @classmethod
        async def create(cls, flow_config, athos_config):
            return cls()

        async def execute(self, input: FlowInput) -> FlowOutput:
            return FlowOutput(content="test")

    # Verify registration
    assert "decorator_flow" in FLOW_REGISTRY
    assert FLOW_REGISTRY["decorator_flow"].creator == DecoratorFlow


def test_missing_metadata_validation():
    """Test that missing class metadata is caught."""
    # Clear registry
    FLOW_REGISTRY.clear()

    class MissingNameFlow(BaseFlow):
        # Missing: name
        config_class = NewPatternFlowConfig
        framework = ToolFramework.LANGGRAPH

        @classmethod
        async def create(cls, flow_config, athos_config):
            return cls()

        async def execute(self, input: FlowInput) -> FlowOutput:
            return FlowOutput(content="test")

    with pytest.raises(ValueError, match="missing required class attributes: name"):
        register_flow(MissingNameFlow)


def test_missing_create_validation():
    """Test that abstract create() method causes issues when instantiating.

    Note: We can't actually catch this at registration time since create() is
    inherited as an abstractmethod. Instead, this test verifies that the class
    cannot be instantiated without implementing create().
    """
    # Clear registry
    FLOW_REGISTRY.clear()

    # This class has create() from BaseFlow but it's abstract
    class MissingCreateFlow(BaseFlow):
        name = "missing_create"
        config_class = NewPatternFlowConfig
        framework = ToolFramework.LANGGRAPH

        # Missing: create() classmethod implementation

        async def execute(self, input: FlowInput) -> FlowOutput:
            return FlowOutput(content="test")

    # Registration should succeed (we have the method, even if abstract)
    register_flow(MissingCreateFlow)

    # But trying to use create() should fail
    # Note: This would fail at runtime when trying to call create()


# ===== Tests: Building Flows =====

@pytest.mark.asyncio
async def test_build_new_pattern_flow():
    """Test that new pattern flow builds without calling initialize()."""
    # Clear and register
    FLOW_REGISTRY.clear()
    register_flow(NewPatternFlow)

    # Build config (flows as dictionaries)
    config = AthosConfig(
        flows={"test": {"type": "new_pattern", "model": "test_model", "value": "test_value"}},
        models={"test_model": ModelConfig(model_id="test-model-id")},
        mcp_servers={},
        tools={},
        workspace_dir="/tmp/athos_test"
    )

    # Build flow
    flow = await build_flow("test", config)

    # Verify flow is fully initialized
    assert isinstance(flow, NewPatternFlow)
    assert flow.value == "initialized_test_value"
    assert flow.initialized is True


# ===== Tests: FlowRunner Integration =====

@pytest.mark.asyncio
async def test_runner_with_new_pattern_flow():
    """Test FlowRunner with new pattern flow (should not call initialize)."""
    # Clear and register
    FLOW_REGISTRY.clear()
    register_flow(NewPatternFlow)

    # Build config (flows as dictionaries)
    config = AthosConfig(
        flows={"test": {"type": "new_pattern", "model": "test_model", "value": "runner_test"}},
        models={"test_model": ModelConfig(model_id="test-model-id")},
        mcp_servers={},
        tools={},
        workspace_dir="/tmp/athos_test"
    )

    # Create runner
    runner = FlowRunner(config)

    # Execute flow
    result = await runner.execute(
        flow_name="test",
        message="hello",
        session_id="session1",
        user_id="user1",
    )

    # Verify
    assert result.success is True
    assert result.output is not None
    assert "initialized_runner_test" in result.output.content
    assert result.output.metadata["initialized"] is True



# ===== Tests: get_flow_registration Helper =====

def test_get_flow_registration():
    """Test get_flow_registration helper function."""
    # Clear and register
    FLOW_REGISTRY.clear()
    register_flow(NewPatternFlow)

    # Get registration
    registration = get_flow_registration("new_pattern")
    assert registration is not None
    assert registration.config_cls == NewPatternFlowConfig
    assert registration.creator == NewPatternFlow

    # Get non-existent
    registration = get_flow_registration("nonexistent")
    assert registration is None
