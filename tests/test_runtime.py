import yaml
from athos.runtime import build_config, build_flow
from athos.flows import ChatbotFlow
from athos.config import AthosConfig
from types import SimpleNamespace
from unittest.mock import Mock


def test_build_config_and_flow(tmp_path, monkeypatch):
    cfg_yaml = """
workspace_dir: "/tmp"
models:
  test_model:
    model_id: "openai/gpt4"
execution_flows:
  chat:
    type: "chatbot"
    model: "test_model"
    system_prompt: "hello"
"""
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(cfg_yaml)
    mock_model = lambda messages, stop_sequences=None: type(
        "Resp", (), {"content": "ok"}
    )()
    monkeypatch.setattr("athos.flows.chatbot.build_model", lambda cfg: mock_model)
    cfg = build_config(str(cfg_file))
    flow = build_flow("chat", cfg)
    assert isinstance(flow, ChatbotFlow)


def test_agent_flow_closes_mcp(tmp_path, monkeypatch):
    cfg_yaml = """
workspace_dir: "/tmp"
models:
  test_model:
    model_id: "openai/gpt4"
mcp_servers:
  s1:
    mcp_type: "mcp_stdio"
    command: "echo"
execution_flows:
  agent:
    type: "agent"
    model: "test_model"
    mcp_servers: [s1]
"""
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(cfg_yaml)
    monkeypatch.setattr("athos.flows.agent.build_model", lambda cfg: lambda m: None)
    dummy_client = SimpleNamespace(disconnect=Mock(), get_tools=lambda: [])
    monkeypatch.setattr("athos.flows.agent.build_mcp_client", lambda n, c: dummy_client)
    cfg = build_config(str(cfg_file))
    flow = build_flow("agent", cfg)
    flow.close()
    dummy_client.disconnect.assert_called_once()


def test_workspace_dir_default_expansion(monkeypatch):
    monkeypatch.delenv("ATHOS_WORKSPACE", raising=False)
    cfg_yaml = 'workspace_dir: "${ATHOS_WORKSPACE:-/tmp/athos_workspace}"\n'
    cfg = AthosConfig.model_validate(yaml.safe_load(cfg_yaml))
    assert cfg.workspace_dir == "/tmp/athos_workspace"


def test_build_config_with_overrides(tmp_path):
    cfg_yaml = """
workspace_dir: "/tmp"
models:
  test_model:
    model_id: "openai/gpt4"
    temperature: 0.7
"""
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(cfg_yaml)
    cfg = build_config(
        str(cfg_file), {"models": {"test_model": {"temperature": 0.2}}}
    )
    assert cfg.models["test_model"].temperature == 0.2
