import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from smolagents import ChatMessage
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "revals",
    Path(__file__).resolve().parents[1] / "evals" / "run_evaluations.py",
)
revals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revals)


def test_multiple_flows_execution(tmp_path, monkeypatch):
    """Ensure run_evaluations executes all provided flows."""

    # create a minimal test case directory
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

    manager = Mock()
    manager.describe_flow.return_value = {}
    manager.config.execution_flows = {
        "f1": SimpleNamespace(model="m1"),
        "f2": SimpleNamespace(model="m2"),
    }
    manager._get_or_create_model.return_value = lambda msgs: ChatMessage(
        role="assistant", content="{\"score\": 1, \"feedback\": \"ok\"}"
    )
    manager.execute_flow = AsyncMock(return_value="resp")
    monkeypatch.setattr(revals, "create_athos_manager", Mock(return_value=manager))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "f2",
            "--cases-dir",
            str(tmp_path),
        ],
    )

    revals.main()

    assert manager.execute_flow.call_count == 2
    called_flows = [c.args[0] for c in manager.execute_flow.call_args_list]
    assert called_flows == ["f1", "f2"]

