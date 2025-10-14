from typing_extensions import Literal

import athos.core.flow_registry as flow_registry
from athos.config.models import BaseFlowConfig


def test_register_flow_and_is_registered(monkeypatch):
    monkeypatch.setattr(flow_registry, "FLOW_REGISTRY", {})

    class DummyFlowConfig(BaseFlowConfig):
        type: Literal["dummy"]

    def factory(cfg, full_cfg):
        return None

    flow_registry.register_flow("dummy", DummyFlowConfig, factory)

    assert "dummy" in flow_registry.FLOW_REGISTRY
    assert flow_registry.FLOW_REGISTRY["dummy"] == (DummyFlowConfig, factory)
    assert flow_registry.is_flow_type_registered("dummy")
    assert not flow_registry.is_flow_type_registered("other")
