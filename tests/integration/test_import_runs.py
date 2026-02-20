import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
EVALS_DIR = REPO_ROOT / "evals"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

spec = importlib.util.spec_from_file_location(
    "import_runs_mod",
    REPO_ROOT / "evals" / "import_runs.py",
)
import_runs_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_runs_mod)


def test_import_runs_writes_canonical_layout(tmp_path, monkeypatch):
    input_path = tmp_path / "external.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "case_one",
                        "agent_system": "codex",
                        "config_id": "cfg123",
                        "dataset_id": "hpc_cases",
                        "run_index": 2,
                        "response": {"output_text": "answer"},
                        "execution": {"status": "success"},
                    }
                )
            ]
        )
    )

    output_dir = tmp_path / "results"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "import_runs",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--experiment-id",
            "exp1",
        ],
    )
    import_runs_mod.main()

    run_path = output_dir / "exp1" / "codex" / "cfg123" / "hpc_cases" / "case_one" / "2" / "run.json"
    assert run_path.exists()
    payload = json.loads(run_path.read_text())
    assert payload["schema_version"] == "athos.run.v1"
    assert payload["experiment_id"] == "exp1"
    assert payload["dataset_id"] == "hpc_cases"
    assert payload["response"]["output_text"] == "answer"


def test_import_runs_rejects_missing_output_for_success(tmp_path, monkeypatch):
    input_path = tmp_path / "bad.json"
    input_path.write_text(
        json.dumps(
            {
                "case_id": "case_one",
                "agent_system": "codex",
                "config_id": "cfg123",
                "execution": {"status": "success"},
            }
        )
    )
    output_dir = tmp_path / "results"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "import_runs",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--experiment-id",
            "exp1",
            "--dataset-id",
            "hpc_cases",
        ],
    )
    with pytest.raises(ValueError, match="success status must include response.output_text"):
        import_runs_mod.main()


def test_import_runs_rejects_unsafe_path_segments(tmp_path, monkeypatch):
    input_path = tmp_path / "bad.json"
    input_path.write_text(
        json.dumps(
            {
                "case_id": "/tmp/escape",
                "agent_system": "codex",
                "config_id": "cfg123",
                "dataset_id": "hpc_cases",
                "execution": {"status": "success"},
                "response": {"output_text": "ok"},
            }
        )
    )
    output_dir = tmp_path / "results"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "import_runs",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--experiment-id",
            "exp1",
        ],
    )
    with pytest.raises(ValueError, match="must be a relative path segment"):
        import_runs_mod.main()
