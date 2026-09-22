from pathlib import Path

import yaml


def test_openwebui_compose_exposes_hpc_consulting_agent_without_docs_rag_flows():
    compose_path = (
        Path(__file__).resolve().parents[3]
        / "integrations"
        / "openwebui"
        / "docker-compose.yml"
    )

    compose = yaml.safe_load(compose_path.read_text())
    pipelines = compose["services"]["pipelines"]
    environment = pipelines["environment"]

    env = dict(item.split("=", 1) for item in environment)
    enabled_flows = env["ATHOS_PIPELINE_ENABLED_FLOWS"].split(",")

    assert env["ATHOS_PIPELINE_DEFAULT_FLOW"] == "lang_hpc_consulting_agent"
    assert "lang_hpc_consulting_agent" in enabled_flows
    assert "lang_docs_agent" not in enabled_flows
    assert "lang_docs_react_agent" not in enabled_flows
    assert "SERVICENOW_INSTANCE_URL" in env
    assert "../../data:/app/data:ro" in pipelines["volumes"]
