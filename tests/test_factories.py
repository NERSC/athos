import sys
import types
import textwrap
import pytest

from pydantic import SecretStr

from athos.factories import build_model, build_tool, build_mcp_client
from athos.config.models import ModelConfig, ToolConfig, MCPServerConfig, MCPType


class DummyTool:
    def __init__(self, value):
        self.value = value


def test_build_model(monkeypatch):
    def dummy_init(self, model_id, api_base=None, api_key=None, **kwargs):
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
    monkeypatch.setattr("athos.factories.OpenAIServerModel.__init__", dummy_init)

    cfg = ModelConfig(
        model_id="openai/gpt4",
        api_base="https://api.test",
        api_key="sek",
    )

    model = build_model(cfg)
    from smolagents import OpenAIServerModel
    assert isinstance(model, OpenAIServerModel)
    assert model.model_id == cfg.model_id
    assert model.api_base == cfg.api_base
    assert model.api_key == cfg.api_key.get_secret_value()


def test_build_tool(monkeypatch):
    module = types.ModuleType("dummy_module")
    module.DummyTool = DummyTool
    sys.modules["dummy_module"] = module

    cfg = ToolConfig(
        callable_name="DummyTool",
        module_path="dummy_module",
        parameters={"value": 42},
    )

    tool = build_tool(cfg)
    assert isinstance(tool, DummyTool)
    assert tool.value == 42


def test_build_tool_decorated_function(tmp_path, monkeypatch):
    module_code = textwrap.dedent(
        '''
        from smolagents import tool

        @tool
        def greet(name: str) -> str:
            """Return a greeting.

            Args:
                name: Name to greet.
            """
            return f"Hello {name}"
        '''
    )
    module_path = tmp_path / "decorated_module.py"
    module_path.write_text(module_code)
    monkeypatch.syspath_prepend(str(tmp_path))

    cfg = ToolConfig(
        callable_name="greet",
        module_path="decorated_module",
        parameters={},
        is_class=False,
    )

    tool = build_tool(cfg)
    assert callable(tool)
    assert tool("World") == "Hello World"


def test_build_mcp_client_stdio(monkeypatch):
    def dummy_init(self, server_parameters):
        self.server_parameters = server_parameters
    monkeypatch.setattr("athos.factories.MCPClient.__init__", dummy_init)

    cfg = MCPServerConfig(
        mcp_type=MCPType.MCP_STDIO,
        command="echo",
        args=["hello"],
        env={"A": "B"},
    )

    client = build_mcp_client("c1", cfg)
    from smolagents import MCPClient
    from mcp import StdioServerParameters
    assert isinstance(client, MCPClient)
    assert isinstance(client.server_parameters, StdioServerParameters)
    assert client.server_parameters.command == "echo"
    assert client.server_parameters.args == ["hello"]
    assert client.server_parameters.env == {"A": "B"}


def test_build_mcp_client_sse(monkeypatch):
    def dummy_init(self, server_parameters):
        self.server_parameters = server_parameters
    monkeypatch.setattr("athos.factories.MCPClient.__init__", dummy_init)

    cfg = MCPServerConfig(
        mcp_type=MCPType.MCP_SSE,
        url="https://server",
        headers={"X": "y"},
    )

    client = build_mcp_client("c2", cfg)
    from smolagents import MCPClient
    assert isinstance(client, MCPClient)
    assert client.server_parameters == {"url": "https://server", "headers": {"X": "y"}}


def test_build_mcp_client_invalid():
    bad_cfg = MCPServerConfig.model_construct(mcp_type="other")
    with pytest.raises(ValueError):
        build_mcp_client("bad", bad_cfg)
