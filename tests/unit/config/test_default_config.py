from athos.runtime.builder import build_config


def test_hpc_consulting_agent_uses_read_only_context_sources(monkeypatch):
    monkeypatch.setenv("CBORG_API_URL", "https://cborg.example.test/v1")
    monkeypatch.setenv("CBORG_API_KEY", "test-key")
    cfg = build_config("config/config.yaml")

    flow = cfg.flows["lang_hpc_consulting_agent"]
    assert flow.type == "langchain_agent"
    assert flow.model == "gptoss"
    assert cfg.models["gptoss"].model_id == "lbl/gpt-oss-120b"
    assert flow.mcp_servers == [
        "servicenow_ro_mcp",
        "consulting_chroma_ro_mcp",
    ]

    servicenow = cfg.mcp_servers["servicenow_ro_mcp"]
    assert servicenow.args == ["--read-only"]
    assert "list_incidents" in servicenow.allowed_tools
    assert "list_groups" in servicenow.allowed_tools
    assert "view_incident_logs" in servicenow.allowed_tools
    assert "create_incident" in servicenow.blocked_tools
    assert "update_incident" in servicenow.blocked_tools
    assert "add_comment" in servicenow.blocked_tools
    assert "resolve_incident" in servicenow.blocked_tools

    chroma = cfg.mcp_servers["consulting_chroma_ro_mcp"]
    assert chroma.args == [
        "--client-type",
        "persistent",
        "--data-dir",
        "data/chroma/aggregates/athos_eval_bundle_20260318_derived_tickets_v2",
    ]
    assert "chroma_query_documents" in chroma.allowed_tools
    assert "chroma_get_documents" in chroma.allowed_tools
    assert "chroma_add_documents" in chroma.blocked_tools
    assert "chroma_delete_collection" in chroma.blocked_tools
