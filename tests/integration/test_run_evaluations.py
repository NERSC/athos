import sys
import json
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from smolagents import ChatMessage
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
EVALS_DIR = REPO_ROOT / "evals"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

from athos.models.flow import FlowOutput
from evals.eval_io import load_qa_cases

spec = importlib.util.spec_from_file_location(
    "revals",
    REPO_ROOT / "evals" / "run_evaluations.py",
)
revals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revals)


async def test_multiple_flows_execution(tmp_path, monkeypatch):
    """Ensure run_evaluations executes all provided flows."""

    # create a minimal test case directory
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

    execute_calls = []

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            execute_calls.append((args, kwargs))
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={},
            )

        async def cleanup(self):
            return None

    class DummyFlowCfg:
        def __init__(self, model):
            self.model = model

        def model_dump(self):
            return {"model": self.model}

    dummy_cfg = SimpleNamespace(
        flows={
            "f1": DummyFlowCfg("m1"),
            "f2": DummyFlowCfg("m2"),
        },
        models={
            "m1": SimpleNamespace(model_id="m1"),
            "m2": SimpleNamespace(model_id="m2"),
        },
        workspace_path=str(tmp_path / "workspace"),
    )
    monkeypatch.setattr(revals, "build_config", Mock(return_value=dummy_cfg))
    monkeypatch.setattr(
        revals.smolagents_factories,
        "build_model",
        lambda cfg: (lambda messages: SimpleNamespace(content="ok")),
    )
    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)

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

    await revals.main()

    assert len(execute_calls) == 2


def test_load_qa_cases(tmp_path):
    qa_file = tmp_path / "cases.jsonl"
    entries = [
        {"name": "c1", "question": "q1", "answer": "a1"},
        {"name": "c2", "question": "q2", "answer": "a2"},
    ]
    with qa_file.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    cases = load_qa_cases(qa_file)
    assert cases == [
        {"name": "c1", "description": "q1", "solution": "a1"},
        {"name": "c2", "description": "q2", "solution": "a2"},
    ]


async def test_qa_file_flow_execution(tmp_path, monkeypatch):
    """Run evaluations with a QA file and ensure results are grouped separately."""

    qa_file = tmp_path / "qa.jsonl"
    entries = [
        {"name": "q1", "question": "What?", "answer": "A1"},
        {"name": "q2", "question": "Why?", "answer": "A2"},
    ]
    with qa_file.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    class DummyFlowCfg:
        def __init__(self, model):
            self.model = model

        def model_dump(self):
            return {"model": self.model}

    dummy_cfg = SimpleNamespace(
        flows={"f1": DummyFlowCfg("m1")},
        models={"m1": SimpleNamespace(model_id="m1")},
        workspace_path=str(tmp_path / "workspace"),
    )
    monkeypatch.setattr(revals, "build_config", Mock(return_value=dummy_cfg))
    monkeypatch.setattr(revals.smolagents_factories, "build_model", lambda cfg: None)
    monkeypatch.setattr(revals, "evaluate_response", lambda m, s, r: (42, "fb"))

    execute_calls = []

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            execute_calls.append((args, kwargs))
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={},
            )

        async def cleanup(self):
            return None

    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)

    output = tmp_path / "out.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--qa-file",
            str(qa_file),
            "--output",
            str(output),
        ],
    )

    await revals.main()

    assert len(execute_calls) == len(entries)

    # Metrics stored under dataset key named after the QA file
    data = json.loads(output.read_text())
    assert "flows" in data
    assert "f1" in data["flows"]
    dataset_key = qa_file.stem
    assert dataset_key in data["flows"]["f1"]
    results = data["flows"]["f1"][dataset_key]["cases"]
    assert len(results) == len(entries)
    assert all("score" in r for r in results)
