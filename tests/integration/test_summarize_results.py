import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
EVALS_DIR = REPO_ROOT / "evals"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

spec = importlib.util.spec_from_file_location(
    "summarize_results_mod",
    REPO_ROOT / "evals" / "summarize_results.py",
)
summarize_results_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize_results_mod)


def _write_run(path: Path, run_id: str, case_id: str, run_index: int) -> None:
    payload = {
        "schema_version": "athos.run.v1",
        "run_id": run_id,
        "experiment_id": "exp1",
        "dataset_id": "cases",
        "dataset_version": None,
        "case_id": case_id,
        "run_index": run_index,
        "agent_system": "athos",
        "agent_version": "git:abc",
        "config_id": "cfg",
        "config_ref": "cfg.yaml",
        "execution": {
            "started_at_utc": "2026-02-15T00:00:00+00:00",
            "finished_at_utc": "2026-02-15T00:00:01+00:00",
            "status": "success",
            "error_type": None,
            "error_message": None,
        },
        "request": {"input_text": "input", "input_artifacts": []},
        "response": {"output_text": "response text", "output_artifacts": []},
        "metrics": {},
        "provenance": {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_summarize_results_groups_and_computes_stats(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(runs_dir / "exp1" / "athos" / "cfg" / "case_one" / "0" / "run.json", "run-1", "case_one", 0)
    _write_run(runs_dir / "exp1" / "athos" / "cfg" / "case_two" / "0" / "run.json", "run-2", "case_two", 0)

    judgments_dir = tmp_path / "judgments"
    judgments_dir.mkdir(parents=True)
    judgments_path = judgments_dir / "judge.jsonl"
    judgments_path.write_text(
        "\n".join(
            [
                json.dumps({"run_id": "run-1", "judgment_status": "scored", "score": 80, "pass": True}),
                json.dumps({"run_id": "run-2", "judgment_status": "scored", "score": 90, "pass": True}),
            ]
        )
    )

    output_path = tmp_path / "summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_results",
            "--runs-dir",
            str(runs_dir),
            "--judgments-dir",
            str(judgments_dir),
            "--output",
            str(output_path),
        ],
    )
    summarize_results_mod.main()

    payload = json.loads(output_path.read_text())
    assert payload["schema_version"] == "athos.summary.v1"
    assert len(payload["aggregates"]) == 1
    agg = payload["aggregates"][0]
    assert agg["experiment_id"] == "exp1"
    assert agg["agent_system"] == "athos"
    assert agg["config_id"] == "cfg"
    assert agg["dataset_id"] == "cases"
    assert agg["run_count"] == 2
    assert agg["scored_count"] == 2
    assert agg["skipped_count"] == 0
    assert agg["skipped_by_reason"] == {}
    assert agg["score_mean"] == 85.0
    assert agg["pass_rate"] == 1.0


def test_summarize_results_counts_skips(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(runs_dir / "exp1" / "athos" / "cfg" / "case_one" / "0" / "run.json", "run-1", "case_one", 0)
    _write_run(runs_dir / "exp1" / "athos" / "cfg" / "case_two" / "0" / "run.json", "run-2", "case_two", 0)

    judgments_dir = tmp_path / "judgments"
    judgments_dir.mkdir(parents=True)
    judgments_path = judgments_dir / "judge.jsonl"
    judgments_path.write_text(
        "\n".join(
            [
                json.dumps({"run_id": "run-1", "judgment_status": "scored", "score": 80, "pass": True}),
                json.dumps(
                    {
                        "run_id": "run-2",
                        "judgment_status": "skipped_missing_output",
                        "score": None,
                        "pass": None,
                    }
                ),
            ]
        )
    )

    output_path = tmp_path / "summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_results",
            "--runs-dir",
            str(runs_dir),
            "--judgments-dir",
            str(judgments_dir),
            "--output",
            str(output_path),
        ],
    )
    summarize_results_mod.main()

    payload = json.loads(output_path.read_text())
    agg = payload["aggregates"][0]
    assert agg["run_count"] == 2
    assert agg["scored_count"] == 1
    assert agg["skipped_count"] == 1
    assert agg["skipped_by_reason"] == {"skipped_missing_output": 1}
    assert agg["score_mean"] == 80.0


def test_summarize_results_ignores_skips_sidecar_file(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(runs_dir / "exp1" / "athos" / "cfg" / "case_one" / "0" / "run.json", "run-1", "case_one", 0)

    judgments_dir = tmp_path / "judgments"
    judgments_dir.mkdir(parents=True)
    (judgments_dir / "judge.jsonl").write_text(
        json.dumps({"run_id": "run-1", "judgment_status": "scored", "score": 75, "pass": False}) + "\n"
    )
    (judgments_dir / "judge.skips.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "athos.skip.v1",
                "run_id": "run-1",
                "reason": "skipped_missing_output",
            }
        )
        + "\n"
    )

    output_path = tmp_path / "summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_results",
            "--runs-dir",
            str(runs_dir),
            "--judgments-dir",
            str(judgments_dir),
            "--output",
            str(output_path),
        ],
    )
    summarize_results_mod.main()

    payload = json.loads(output_path.read_text())
    # Only one real judgment source should be listed; .skips.jsonl sidecar is ignored.
    assert len(payload["judgment_sources"]) == 1
    assert payload["judgment_sources"][0].endswith("judge.jsonl")
