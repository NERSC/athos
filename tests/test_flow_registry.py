from typing_extensions import Literal

import athos.registry.flow_registry as flow_registry
from athos.config.models import BaseFlowConfig, ToolFramework


def test_register_flow_and_is_registered(monkeypatch):
    monkeypatch.setattr(flow_registry, "FLOW_REGISTRY", {})

    class DummyFlowConfig(BaseFlowConfig):
        type: Literal["dummy"]

    def factory(cfg, full_cfg):
        return None

    flow_registry.register_flow(
        "dummy", DummyFlowConfig, factory, framework=ToolFramework.SMOLAGENTS
    )

    assert "dummy" in flow_registry.FLOW_REGISTRY
    registration = flow_registry.FLOW_REGISTRY["dummy"]
    assert registration.config_cls is DummyFlowConfig
    assert registration.factory is factory
    assert registration.framework is ToolFramework.SMOLAGENTS
    assert flow_registry.is_flow_type_registered("dummy")
    assert not flow_registry.is_flow_type_registered("other")
