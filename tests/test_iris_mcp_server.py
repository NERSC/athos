import json

import pytest

from athos.tools.iris_mcp import server as iris_server


def test_load_config_env(monkeypatch):
    monkeypatch.setenv("IRIS_BASE_URL", "https://example.com")
    cfg = iris_server.load_config()
    assert cfg["base_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_get_users(monkeypatch):
    async def fake_execute(query, variables=None):
        assert variables == {"username": "User"}
        return {
            "data": {
                "systemInfo": {
                    "users": [
                        {"uid": 1, "email": "user@example.com", "name": "User"}
                    ]
                }
            }
        }

    monkeypatch.setattr(iris_server.iris_client, "execute_query", fake_execute)

    tool = await iris_server.mcp.get_tool("get_users")
    result = await tool.run({"username": "User"})
    data = json.loads(result.content[0].text)
    assert data["data"]["systemInfo"]["users"][0]["uid"] == 1
