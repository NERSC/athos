import sys
import json
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import importlib.util
from pathlib import Path

from pydantic import SecretStr

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


def test_compute_config_id_handles_secretstr_model_fields():
    class DummyFlowCfg:
        def __init__(self, model):
            self.model = model

        def model_dump(self, *args, **kwargs):
            return {"model": self.model}

    class DummyModelCfg:
        def __init__(self, model_id):
            self.model_id = model_id
            self.api_key = SecretStr("top-secret")

        def model_dump(self, *args, **kwargs):
            return {"model_id": self.model_id, "api_key": self.api_key}

    config_id_a = revals._compute_config_id("f1", DummyFlowCfg("m1"), DummyModelCfg("provider/model-a"))
    config_id_a_repeat = revals._compute_config_id("f1", DummyFlowCfg("m1"), DummyModelCfg("provider/model-a"))
    config_id_b = revals._compute_config_id("f1", DummyFlowCfg("m1"), DummyModelCfg("provider/model-b"))

    assert config_id_a.startswith("f1__m1__")
    assert config_id_a == config_id_a_repeat
    assert config_id_a != config_id_b


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
            "--output-dir",
            str(tmp_path / "results"),
            "--experiment-id",
            "exp1",
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

    output_root = tmp_path / "results"

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
            "--output-dir",
            str(output_root),
            "--experiment-id",
            "exp1",
        ],
    )

    await revals.main()

    assert len(execute_calls) == len(entries)
    run_records = sorted((output_root / "exp1" / "athos").glob("*/*/*/*/run.json"))
    assert len(run_records) == len(entries)
    for run_path in run_records:
        payload = json.loads(run_path.read_text())
        assert payload["dataset_id"] == qa_file.stem
        assert payload["execution"]["status"] == "success"


async def test_canonical_run_layout(tmp_path, monkeypatch):
    """Ensure canonical run layout is written."""

    case_dir = tmp_path / "cases" / "case_one"
    case_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

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

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            execute_calls.append(1)
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={"latency_ms": 10.0},
            )

        async def cleanup(self):
            return None

    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)
    execute_calls = []
    monkeypatch.setattr(
        revals.subprocess,
        "check_output",
        lambda *args, **kwargs: b"abcdef123456\n",
    )

    canonical_root = tmp_path / "results"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(canonical_root),
            "--experiment-id",
            "exp1",
        ],
    )

    await revals.main()

    run_path = canonical_root / "exp1" / "athos"
    run_records = list(run_path.glob("*/*/*/*/run.json"))
    assert len(run_records) == 1
    run_payload = json.loads(run_records[0].read_text())
    assert run_payload["schema_version"] == "athos.run.v1"
    assert run_payload["experiment_id"] == "exp1"
    assert run_payload["agent_system"] == "athos"
    assert run_payload["case_id"] == "case_one"
    assert run_payload["run_index"] == 0
    assert run_payload["response"]["output_text"] == "resp"
    assert run_payload["execution"]["status"] == "success"


async def test_run_start_writes_new_run_dirs_without_overwrite(tmp_path, monkeypatch):
    """Ensure later runs can append run indices without mutating existing runs."""

    case_dir = tmp_path / "cases" / "case_one"
    case_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

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

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={"latency_ms": 10.0},
            )

        async def cleanup(self):
            return None

    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)
    monkeypatch.setattr(
        revals.subprocess,
        "check_output",
        lambda *args, **kwargs: b"abcdef123456\n",
    )

    canonical_root = tmp_path / "results"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(canonical_root),
            "--experiment-id",
            "exp1",
        ],
    )
    await revals.main()

    first_run = next((canonical_root / "exp1" / "athos").glob("*/*/*/0/run.json"))
    first_contents = first_run.read_text()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(canonical_root),
            "--experiment-id",
            "exp1",
            "--run-start",
            "1",
            "--run-count",
            "2",
        ],
    )
    await revals.main()

    root = canonical_root / "exp1" / "athos"
    run_records = sorted(root.glob("*/*/*/*/run.json"))
    assert len(run_records) == 3
    run_indices = sorted(json.loads(path.read_text())["run_index"] for path in run_records)
    assert run_indices == [0, 1, 2]
    assert first_run.read_text() == first_contents


async def test_empty_response_marked_invalid_and_not_judged(tmp_path, monkeypatch):
    """Blank output should be marked invalid_output."""

    case_dir = tmp_path / "cases" / "case_one"
    case_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

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

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="   "),
                error=None,
                metadata={"latency_ms": 10.0},
            )

        async def cleanup(self):
            return None

    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)
    output_root = tmp_path / "results"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(output_root),
            "--experiment-id",
            "exp1",
        ],
    )

    await revals.main()

    run_path = next((output_root / "exp1" / "athos").glob("*/*/*/*/run.json"))
    payload = json.loads(run_path.read_text())
    assert payload["execution"]["status"] == "invalid_output"
    assert payload["execution"]["error_type"] == "empty_response"


async def test_inline_scoring_fields_removed(tmp_path, monkeypatch):
    """Results should not include inline scoring fields."""

    case_dir = tmp_path / "cases" / "case_one"
    case_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

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

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={"latency_ms": 10.0},
            )

        async def cleanup(self):
            return None

    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)

    output_root = tmp_path / "results"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(output_root),
            "--experiment-id",
            "exp1",
        ],
    )

    await revals.main()

    run_path = next((output_root / "exp1" / "athos").glob("*/*/*/*/run.json"))
    payload = json.loads(run_path.read_text())
    assert "score" not in payload
    assert "feedback" not in payload
    assert payload["execution"]["status"] == "success"


async def test_duplicate_run_path_fails_without_overwrite_flag(tmp_path, monkeypatch):
    """Writing an existing canonical run.json should fail by default."""

    case_dir = tmp_path / "cases" / "case_one"
    case_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

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
    monkeypatch.setattr(
        revals.subprocess,
        "check_output",
        lambda *args, **kwargs: b"abcdef123456\n",
    )
    execute_calls = []

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            execute_calls.append(1)
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={"latency_ms": 10.0},
            )

        async def cleanup(self):
            return None

    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)

    canonical_root = tmp_path / "results"
    argv = [
        "revals",
        "--config",
        "cfg.yaml",
        "--flow",
        "f1",
        "--cases-dir",
        str(tmp_path / "cases"),
        "--output-dir",
        str(canonical_root),
        "--experiment-id",
        "exp1",
    ]

    monkeypatch.setattr(sys, "argv", argv)
    await revals.main()
    assert len(execute_calls) == 1

    monkeypatch.setattr(sys, "argv", argv)
    try:
        await revals.main()
        raise AssertionError("Expected FileExistsError for duplicate canonical run path")
    except FileExistsError:
        pass
    # Second invocation should fail before running the flow.
    assert len(execute_calls) == 1


async def test_run_evaluations_rejects_unsafe_case_id_for_output_path(tmp_path, monkeypatch):
    qa_file = tmp_path / "qa.jsonl"
    qa_file.write_text(
        json.dumps(
            {
                "name": "../../outside",
                "question": "q1",
                "answer": "a1",
            }
        )
        + "\n"
    )

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
    monkeypatch.setattr(
        revals.subprocess,
        "check_output",
        lambda *args, **kwargs: b"abcdef123456\n",
    )

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={"latency_ms": 10.0},
            )

        async def cleanup(self):
            return None

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
            "--qa-file",
            str(qa_file),
            "--output-dir",
            str(tmp_path / "results"),
            "--experiment-id",
            "exp1",
        ],
    )

    try:
        await revals.main()
        raise AssertionError("Expected ValueError for unsafe case_id path segment")
    except ValueError as exc:
        assert "case_id" in str(exc)


async def test_run_evaluations_rejects_unsafe_experiment_or_agent_segments(tmp_path, monkeypatch):
    case_dir = tmp_path / "cases" / "case_one"
    case_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

    class DummyFlowCfg:
        def __init__(self, model):
            self.model = model

        def model_dump(self):
            return {"model": self.model}

    dummy_cfg = SimpleNamespace(
        flows={"f1": DummyFlowCfg("m1")},
        models={"m1": SimpleNamespace(model_id="m1", model_dump=lambda: {"model_id": "m1"})},
        workspace_path=str(tmp_path / "workspace"),
    )
    monkeypatch.setattr(revals, "build_config", Mock(return_value=dummy_cfg))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(tmp_path / "results"),
            "--experiment-id",
            "../bad",
        ],
    )
    try:
        await revals.main()
        raise AssertionError("Expected ValueError for unsafe experiment_id")
    except ValueError as exc:
        assert "experiment_id" in str(exc)


async def test_config_id_changes_when_model_config_changes(tmp_path, monkeypatch):
    case_dir = tmp_path / "cases" / "case_one"
    case_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("desc")
    (case_dir / "solution.md").write_text("sol")

    class DummyFlowCfg:
        def __init__(self, model):
            self.model = model

        def model_dump(self):
            return {"model": self.model}

    class DummyModelCfg:
        def __init__(self, model_id):
            self.model_id = model_id

        def model_dump(self):
            return {"model_id": self.model_id}

    class DummyRunner:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *args, **kwargs):
            return SimpleNamespace(
                success=True,
                output=FlowOutput(content="resp"),
                error=None,
                metadata={"latency_ms": 10.0},
            )

        async def cleanup(self):
            return None

    monkeypatch.setattr(revals, "FlowRunner", DummyRunner)
    monkeypatch.setattr(
        revals.subprocess,
        "check_output",
        lambda *args, **kwargs: b"abcdef123456\n",
    )

    root = tmp_path / "results"

    cfg_a = SimpleNamespace(
        flows={"f1": DummyFlowCfg("m1")},
        models={"m1": DummyModelCfg("provider/model-a")},
        workspace_path=str(tmp_path / "workspace"),
    )
    monkeypatch.setattr(revals, "build_config", Mock(return_value=cfg_a))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(root),
            "--experiment-id",
            "exp1",
        ],
    )
    await revals.main()

    cfg_b = SimpleNamespace(
        flows={"f1": DummyFlowCfg("m1")},
        models={"m1": DummyModelCfg("provider/model-b")},
        workspace_path=str(tmp_path / "workspace"),
    )
    monkeypatch.setattr(revals, "build_config", Mock(return_value=cfg_b))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "revals",
            "--config",
            "cfg.yaml",
            "--flow",
            "f1",
            "--cases-dir",
            str(tmp_path / "cases"),
            "--output-dir",
            str(root),
            "--experiment-id",
            "exp1",
            "--run-start",
            "1",
        ],
    )
    await revals.main()

    config_dirs = [p.name for p in (root / "exp1" / "athos").iterdir() if p.is_dir()]
    assert len(config_dirs) == 2
