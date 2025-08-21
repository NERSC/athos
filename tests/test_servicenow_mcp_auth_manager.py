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
