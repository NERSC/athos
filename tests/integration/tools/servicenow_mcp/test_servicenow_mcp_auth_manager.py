from unittest.mock import Mock

from athos.tools.servicenow_mcp.auth.auth_manager import AuthManager
from athos.tools.servicenow_mcp.utils.config import AuthConfig, AuthType, OAuthConfig


def test_oauth_token_url_constructed_from_instance(monkeypatch):
    oauth_cfg = OAuthConfig(
        client_id="id",
        client_secret="secret",
        username="user",
        password="pass",
        instance_url="https://example.service-now.com",
    )
    auth_cfg = AuthConfig(type=AuthType.OAUTH, oauth=oauth_cfg)
    manager = AuthManager(auth_cfg)

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"access_token": "tok", "token_type": "Bearer"}

    def fake_post(url, data):
        assert url == "https://example.service-now.com/oauth_token.do"
        return mock_response

    monkeypatch.setattr(
        "athos.tools.servicenow_mcp.auth.auth_manager.requests.post", fake_post
    )

    manager._get_oauth_token()

    assert manager.token == "tok"
    assert manager.token_type == "Bearer"


def test_get_headers_refreshes_expired_token(monkeypatch):
    oauth_cfg = OAuthConfig(
        client_id="id",
        client_secret="secret",
        username="user",
        password="pass",
        instance_url="https://example.service-now.com",
    )
    auth_cfg = AuthConfig(type=AuthType.OAUTH, oauth=oauth_cfg)
    manager = AuthManager(auth_cfg)

    responses = [
        {"access_token": "tok1", "token_type": "Bearer", "expires_in": 1},
        {"access_token": "tok2", "token_type": "Bearer", "expires_in": 1},
    ]
    call_count = {"count": 0}

    def fake_post(url, data):
        resp = Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = responses[call_count["count"]]
        call_count["count"] += 1
        return resp

    monkeypatch.setattr(
        "athos.tools.servicenow_mcp.auth.auth_manager.requests.post", fake_post
    )

    headers1 = manager.get_headers()
    assert headers1["Authorization"] == "Bearer tok1"

    # Simulate expiry
    manager.expires_at = 0

    headers2 = manager.get_headers()
    assert headers2["Authorization"] == "Bearer tok2"
    assert call_count["count"] == 2

