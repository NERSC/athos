import sys
import json
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from smolagents import ChatMessage
import importlib.util
from pathlib import Path

from athos.models.flow import FlowOutput

spec = importlib.util.spec_from_file_location(
    "revals",
    Path(__file__).resolve().parents[1] / "evals" / "run_evaluations.py",
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

    created_flows = []

    async def _make_flow(*args, **kwargs):
        f = AsyncMock()
        f.execute.return_value = FlowOutput(content="resp")
        f.cleanup = AsyncMock()
        created_flows.append(f)
        return f

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
    monkeypatch.setattr(revals, "build_flow", Mock(side_effect=_make_flow))

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

    # First two created flows correspond to the user flows
    for f in created_flows[:2]:
        assert f.execute.call_count == 1
        assert f.cleanup.call_count == 1


def test_load_qa_cases(tmp_path):
    qa_file = tmp_path / "cases.jsonl"
    entries = [
        {"name": "c1", "question": "q1", "answer": "a1"},
        {"name": "c2", "question": "q2", "answer": "a2"},
    ]
    with qa_file.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    cases = revals.load_qa_cases(qa_file)
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

    created_flows = []

    async def _make_flow(*args, **kwargs):
        f = AsyncMock()
        f.execute.return_value = FlowOutput(content="resp")
        f.cleanup = AsyncMock()
        created_flows.append(f)
        return f

    monkeypatch.setattr(revals, "build_flow", Mock(side_effect=_make_flow))

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

    # Flow executed once per QA pair
    assert len(created_flows) == 1
    flow = created_flows[0]
    assert flow.execute.call_count == len(entries)

    # Metrics stored under dataset key named after the QA file
    data = json.loads(output.read_text())
    assert "f1" in data
    dataset_key = qa_file.stem
    assert dataset_key in data["f1"]
    results = data["f1"][dataset_key]
    assert len(results) == len(entries)
    assert all("score" in r for r in results)


async def test_metrics_recorded_and_aggregated(tmp_path, monkeypatch, capsys):
    """Ensure metrics are persisted per test and aggregated in the report."""

    qa_file = tmp_path / "qa.jsonl"
    entries = [
        {"name": "q1", "question": "First?", "answer": "A1"},
        {"name": "q2", "question": "Second?", "answer": "A2"},
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
    monkeypatch.setattr(revals, "evaluate_response", lambda m, s, r: (95, "fb"))

    responses = [
        FlowOutput(
            content="resp1",
            metadata={
                "token_usage": {"input_tokens": 10, "output_tokens": 5},
                "latency_ms": 120,
                "tool_calls": [{"name": "search", "call_count": 2}],
            },
        ),
        FlowOutput(
            content="resp2",
            metadata={
                "token_usage": {"input_tokens": 20, "output_tokens": 10},
                "latency_ms": 200,
                "tool_calls": [
                    {"name": "search", "call_count": 1},
                    {"name": "calc", "call_count": 3},
                ],
            },
        ),
    ]

    async def _make_flow(*args, **kwargs):
        f = AsyncMock()
        f.execute = AsyncMock(side_effect=responses)
        f.cleanup = AsyncMock()
        return f

    monkeypatch.setattr(revals, "build_flow", Mock(side_effect=_make_flow))

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

    captured = capsys.readouterr().out

    data = json.loads(output.read_text())
    results = data["f1"][qa_file.stem]

    assert all("metrics" in r for r in results)
    assert all("token_usage" in r["metrics"] for r in results)
    assert all("latency_ms" in r["metrics"] for r in results)
    assert all("tool_calls" in r["metrics"] for r in results)

    # Aggregated report should include token, latency, and tool call summaries
    assert "Token Usage:" in captured
    assert "Latency:" in captured
    assert "Tool Calls:" in captured

    # Totals are summed across test cases
    assert "Total: 45 tokens" in captured
    assert "Total: 320 ms" in captured
    assert "search: 3 calls" in captured
    assert "calc: 3 calls" in captured
