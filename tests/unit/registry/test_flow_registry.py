from typing_extensions import Literal
import pytest

import athos.registry.flow_registry as flow_registry
from athos.config.models import BaseFlowConfig, ToolFramework, AthosConfig
from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput


def test_register_flow_and_is_registered(monkeypatch):
    monkeypatch.setattr(flow_registry, "FLOW_REGISTRY", {})

    class DummyFlowConfig(BaseFlowConfig):
        type: Literal["dummy"]

    class DummyFlow(BaseFlow):
        name = "dummy"
        config_class = DummyFlowConfig
        framework = ToolFramework.SMOLAGENTS

        @classmethod
        async def create(cls, flow_config, athos_config):
            return cls()

        async def execute(self, input: FlowInput) -> FlowOutput:
            return FlowOutput(content="dummy")

    flow_registry.register_flow(DummyFlow)

    assert "dummy" in flow_registry.FLOW_REGISTRY
    registration = flow_registry.FLOW_REGISTRY["dummy"]
    assert registration.config_cls is DummyFlowConfig
    assert registration.creator is DummyFlow
    assert registration.framework is ToolFramework.SMOLAGENTS
    assert flow_registry.is_flow_type_registered("dummy")
    assert not flow_registry.is_flow_type_registered("other")
