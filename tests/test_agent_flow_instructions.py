from athos.flows.agent import AgentFlow, AgentFlowConfig, create_agent_flow
from athos.config.models import AthosConfig, ModelConfig, MCPServerConfig, MCPType


def test_create_agent_flow_appends_mcp_instructions(monkeypatch):
    instructions = "Please comply"
    mcp_instruction = "Use docs tool"

    # provide dummy model builder to avoid real initialization
    class DummyModel:
        pass

    def fake_build_model(cfg):
        return DummyModel()

    def fake_build_mcp_client(name, cfg):
        class DummyClient:
            def get_tools(self):
                return []
        return DummyClient()

    monkeypatch.setattr("athos.flows.agent.build_model", fake_build_model)
    monkeypatch.setattr("athos.flows.agent.build_mcp_client", fake_build_mcp_client)

    # simplify CodeAgent.__init__ to record instructions
    def dummy_agent_init(self, tools, model, **kwargs):
        self.instructions = kwargs.get("instructions")

    monkeypatch.setattr("athos.flows.agent.CodeAgent.__init__", dummy_agent_init)

    cfg = AgentFlowConfig(
        type="agent",
        model="m1",
        instructions=instructions,
        mcp_servers=["mcp1"],
    )
    full_cfg = AthosConfig(
        models={"m1": ModelConfig(model_id="id")},
        tools={},
        mcp_servers={
            "mcp1": MCPServerConfig(
                mcp_type=MCPType.MCP_STDIO,
                command="cmd",
                instructions=mcp_instruction,
            )
        },
        flows={},
        workspace_dir="/tmp",
    )

    flow = create_agent_flow(cfg, full_cfg)
    assert isinstance(flow, AgentFlow)
    assert flow.agent.instructions == instructions + "\n\n" + mcp_instruction
