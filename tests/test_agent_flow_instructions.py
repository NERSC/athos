from athos.flows.agent import AgentFlow, AgentFlowConfig, create_agent_flow
from athos.config.models import AthosConfig, ModelConfig


def test_create_agent_flow_passes_instructions(monkeypatch):
    instructions = "Please comply"

    # provide dummy model builder to avoid real initialization
    class DummyModel:
        pass

    def fake_build_model(cfg):
        return DummyModel()

    monkeypatch.setattr("athos.flows.agent.build_model", fake_build_model)

    # simplify CodeAgent.__init__ to record instructions
    def dummy_agent_init(self, tools, model, **kwargs):
        self.instructions = kwargs.get("instructions")

    monkeypatch.setattr("athos.flows.agent.CodeAgent.__init__", dummy_agent_init)

    cfg = AgentFlowConfig(type="agent", model="m1", instructions=instructions)
    full_cfg = AthosConfig(models={"m1": ModelConfig(model_id="id")}, tools={}, mcp_servers={}, execution_flows={})

    flow = create_agent_flow(cfg, full_cfg)
    assert isinstance(flow, AgentFlow)
    assert flow.agent.instructions == instructions
