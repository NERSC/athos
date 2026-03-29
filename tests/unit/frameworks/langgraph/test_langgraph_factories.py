import sys
import types
import textwrap

import pytest

from athos.config.models import (
    MCPServerConfig,
    MCPType,
    ModelConfig,
    ToolConfig,
    ToolFramework,
)
from athos.frameworks.langgraph import factories


class DummyChatOpenAI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyTool:
    def __init__(self, value):
        self.value = value


class DummyMultiServerMCPClient:
    def __init__(self, servers):
        self.servers = servers


@pytest.fixture(autouse=True)
def reset_factories_modules(monkeypatch):
    """Ensure optional dependencies can be substituted in each test."""

    monkeypatch.setattr(factories, "ChatOpenAI", DummyChatOpenAI)
    monkeypatch.setattr(factories, "MultiServerMCPClient", DummyMultiServerMCPClient)


def test_build_model_constructs_chat_model():
    cfg = ModelConfig(
        model_id="gpt-4o",
        api_key="sek",
        api_base="https://api.test",
        temperature=0.25,
        max_tokens=256,
        system_prompt="You are helpful.",
    )

    model = factories.build_model(cfg)

    assert isinstance(model, DummyChatOpenAI)
    assert model.kwargs == {
        "model": "gpt-4o",
        "temperature": 0.25,
        "max_tokens": 256,
        "api_key": "sek",
        "base_url": "https://api.test",
        "default_system_prompt": "You are helpful.",
    }


def test_build_tool_instantiates_class(tmp_path, monkeypatch):
    module = types.ModuleType("dummy_module")
    module.DummyTool = DummyTool
    sys.modules["dummy_module"] = module

    cfg = ToolConfig(
        callable_name="DummyTool",
        module_path="dummy_module",
        parameters={"value": 7},
        framework=ToolFramework.LANGGRAPH,
    )

    tool = factories.build_tool(cfg)

    assert isinstance(tool, DummyTool)
    assert tool.value == 7


def test_build_tool_decorated_function(tmp_path, monkeypatch):
    module_code = textwrap.dedent(
        """
        from langchain_core.tools import tool

        @tool
        def greet(name: str) -> str:
            return f"Hello {name}!"
        """
    )
    module_path = tmp_path / "langgraph_decorated_module.py"
    module_path.write_text(module_code)
    monkeypatch.syspath_prepend(str(tmp_path))

    # Provide a minimal "langchain_core.tools" module exposing ``tool`` decorator.
    tools_module = types.ModuleType("langchain_core.tools")

    def passthrough_decorator(fn):
        return fn

    tools_module.tool = passthrough_decorator
    sys.modules["langchain_core.tools"] = tools_module

    cfg = ToolConfig(
        callable_name="greet",
        module_path="langgraph_decorated_module",
        parameters={},
        is_class=False,
        framework=ToolFramework.LANGGRAPH,
    )

    tool = factories.build_tool(cfg)

    assert callable(tool)
    assert tool("World") == "Hello World!"


def test_build_tool_non_class_factory_receives_parameters(tmp_path, monkeypatch):
    module_code = textwrap.dedent(
        """
        def make_tool(*, prefix: str):
            def tool(name: str) -> str:
                return f"{prefix}:{name}"
            return tool
        """
    )
    module_path = tmp_path / "langgraph_factory_module.py"
    module_path.write_text(module_code)
    monkeypatch.syspath_prepend(str(tmp_path))

    cfg = ToolConfig(
        callable_name="make_tool",
        module_path="langgraph_factory_module",
        parameters={"prefix": "cfg"},
        is_class=False,
        framework=ToolFramework.LANGGRAPH,
    )

    tool = factories.build_tool(cfg)

    assert callable(tool)
    assert tool("World") == "cfg:World"


def test_build_mcp_client_stdio():
    cfg = MCPServerConfig(
        mcp_type=MCPType.MCP_STDIO,
        command="echo",
        args=["hello"],
        env={"A": "B"},
    )

    client = factories.build_mcp_client("stdio-server", cfg)

    assert isinstance(client, DummyMultiServerMCPClient)
    assert client.servers == {
        "stdio-server": {
            "transport": "stdio",
            "command": "echo",
            "args": ["hello"],
            "env": {"A": "B"},
        }
    }


def test_build_mcp_client_sse():
    cfg = MCPServerConfig(
        mcp_type=MCPType.MCP_SSE,
        url="https://mcp.test",
        headers={"Auth": "token"},
    )

    client = factories.build_mcp_client("sse-server", cfg)

    assert isinstance(client, DummyMultiServerMCPClient)
    assert client.servers == {
        "sse-server": {
            "transport": "sse",
            "url": "https://mcp.test",
            "headers": {"Auth": "token"},
        }
    }


def test_build_mcp_client_invalid_type():
    cfg = MCPServerConfig.model_construct(mcp_type="unsupported")

    with pytest.raises(ValueError):
        factories.build_mcp_client("bad", cfg)


def test_build_tool_rejects_mismatched_framework():
    module = types.ModuleType("dummy_module")
    module.DummyTool = DummyTool
    sys.modules["dummy_module"] = module

    cfg = ToolConfig(
        callable_name="DummyTool",
        module_path="dummy_module",
        parameters={"value": 7},
        framework=ToolFramework.SMOLAGENTS,
    )

    with pytest.raises(ValueError, match="framework 'smolagents'"):
        factories.build_tool(cfg)
