import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location(
    "check_cborg_models_mod",
    REPO_ROOT / "scripts" / "check_cborg_models.py",
)
check_cborg_models_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_cborg_models_mod)


def test_try_chat_completion_uses_v1_chat_completions(monkeypatch):
    seen = {}

    def _fake_request_json(url, api_key, method="GET", payload=None):
        seen["url"] = url
        seen["method"] = method
        return {"id": "ok"}

    monkeypatch.setattr(check_cborg_models_mod, "_request_json", _fake_request_json)

    ok, detail = check_cborg_models_mod.try_chat_completion(
        "https://api.example.test",
        "test-key",
        "demo-model",
    )

    assert ok is True
    assert detail == "ok"
    assert seen["method"] == "POST"
    assert seen["url"] == "https://api.example.test/v1/chat/completions"
