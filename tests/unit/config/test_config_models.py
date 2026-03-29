import pytest

from athos.config.models import AthosConfig
# Import flows to ensure they are registered
from athos.frameworks.smolagents import flows as smol_flows  # noqa: F401
from athos.frameworks.langgraph import flows as lg_flows  # noqa: F401


def test_smol_flow_rejects_langgraph_tool():
    config_data = {
        "workspace_dir": "/tmp",
        "models": {"m": {"model_id": "demo"}},
        "tools": {
            "lang_tool": {
                "callable_name": "Tool",
                "module_path": "demo.tool",
                "framework": "langgraph",
            }
        },
        "flows": {
            "bad_agent": {
                "type": "smol_agent",
                "model": "m",
                "tools": ["lang_tool"],
            }
        },
    }

    with pytest.raises(ValueError, match="requires tools configured for 'smolagents'"):
        AthosConfig.model_validate(config_data)


def test_langgraph_flow_rejects_smol_tool():
    config_data = {
        "workspace_dir": "/tmp",
        "models": {"m": {"model_id": "demo"}},
        "tools": {
            "smol_tool": {
                "callable_name": "Tool",
                "module_path": "demo.tool",
                "framework": "smolagents",
            }
        },
        "flows": {
            "bad_langgraph": {
                "type": "langchain_agent",
                "model": "m",
                "tools": ["smol_tool"],
            }
        },
    }

    with pytest.raises(ValueError, match="requires tools configured for 'langgraph'"):
        AthosConfig.model_validate(config_data)


def test_tool_parameters_expand_env_vars(monkeypatch):
    monkeypatch.setenv("ATHOS_WORKSPACE", "/tmp/athos-workspace")

    config_data = {
        "workspace_dir": "/tmp",
        "models": {"m": {"model_id": "demo"}},
        "tools": {
            "search": {
                "callable_name": "create_search_file_contents_tool",
                "module_path": "athos.tools.filesystem_search",
                "framework": "langgraph",
                "is_class": False,
                "parameters": {
                    "allowed_root": "${ATHOS_WORKSPACE}/file_retrieval_corpus",
                    "nested": {
                        "path": "${ATHOS_WORKSPACE}/nested"
                    },
                },
            }
        },
        "flows": {
            "ok_langgraph": {
                "type": "langchain_agent",
                "model": "m",
                "tools": ["search"],
            }
        },
    }

    cfg = AthosConfig.model_validate(config_data)

    assert cfg.tools["search"].parameters["allowed_root"] == "/tmp/athos-workspace/file_retrieval_corpus"
    assert cfg.tools["search"].parameters["nested"]["path"] == "/tmp/athos-workspace/nested"
