import json
import pytest

from athos.tools.iris_mcp import server as iris_server


def test_load_config_env(monkeypatch):
    monkeypatch.setenv("IRIS_BASE_URL", "https://example.com")
    cfg = iris_server.load_config()
    assert cfg["base_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_get_user_info(monkeypatch):
    async def fake_execute(query, variables=None):
        assert variables == {"username": "User"}
        return {
            "data": {
                "systemInfo": {
                    "users": [
                        {
                            "id": 1,
                            "uid": 1,
                            "email": "user@example.com",
                            "name": "User",
                            "projects": [],
                            "groups": [],
                        }
                    ]
                }
            }
        }

    monkeypatch.setattr(iris_server.iris_client, "execute_query", fake_execute)

    tool = await iris_server.mcp.get_tool("get_user_info")
    result = await tool.run({"username": "User"})
    data = json.loads(result.content[0].text)
    assert data["data"]["systemInfo"]["users"][0]["uid"] == 1


@pytest.mark.asyncio
async def test_get_project_info(monkeypatch):
    async def fake_execute(query, variables=None):
        assert variables == {"pname": "m1234"}
        return {
            "data": {
                "systemInfo": {
                    "projects": [
                        {
                            "id": 42,
                            "status": "active",
                            "quotas": [{"store": "scratch", "inode": 100}],
                            "projectUsers": [
                                {
                                    "role": "pi",
                                    "user": {"uid": 1, "name": "User", "email": "u@e"},
                                }
                            ],
                        }
                    ]
                }
            }
        }

    monkeypatch.setattr(iris_server.iris_client, "execute_query", fake_execute)

    tool = await iris_server.mcp.get_tool("get_project_info")
    result = await tool.run({"pname": "m1234"})
    data = json.loads(result.content[0].text)
    project = data["data"]["systemInfo"]["projects"][0]
    assert project["id"] == 42
    assert project["projectUsers"][0]["user"]["uid"] == 1
