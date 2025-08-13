import os
from athos.config.models import MCPServerConfig, MCPType

def test_mcp_server_args_env(monkeypatch):
    monkeypatch.setenv('RAG_DIR', '/custom/path')
    cfg = MCPServerConfig(
        mcp_type=MCPType.MCP_STDIO,
        command='rag-mcp',
        args=['--docs-path', '${RAG_DIR}']
    )
    assert cfg.args == ['--docs-path', '/custom/path']
