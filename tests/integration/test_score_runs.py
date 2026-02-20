import json
import sys
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
EVALS_DIR = REPO_ROOT / "evals"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

spec = importlib.util.spec_from_file_location(
    "score_runs_mod",
    REPO_ROOT / "evals" / "score_runs.py",
)
score_runs_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score_runs_mod)


def _write_run(path: Path, run_id: str, case_id: str, output_text: str) -> None:
    payload = {
        "schema_version": "athos.run.v1",
        "run_id": run_id,
        "experiment_id": "exp1",
        "dataset_id": "cases",
        "dataset_version": None,
        "case_id": case_id,
        "run_index": 0,
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
        "request": {
            "input_text": "input",
            "input_artifacts": [],
        },
        "response": {
            "output_text": output_text,
            "output_artifacts": [],
        },
        "metrics": {},
        "provenance": {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_score_runs_scores_canonical_runs(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text="response text",
    )

    case_root = tmp_path / "cases" / "case_one"
    case_root.mkdir(parents=True)
    (case_root / "user_description.txt").write_text("desc")
    (case_root / "solution.md").write_text("expected answer")

    dummy_cfg = SimpleNamespace(
        models={"judge_model": SimpleNamespace(model_id="judge_model")}
    )
    monkeypatch.setattr(score_runs_mod, "build_config", Mock(return_value=dummy_cfg))
    monkeypatch.setattr(
        score_runs_mod.smolagents_factories,
        "build_model",
        lambda _cfg: object(),
    )
    monkeypatch.setattr(
        score_runs_mod,
        "evaluate_response",
        lambda _model, _sol, _resp: (88, "good"),
    )

    out_jsonl = tmp_path / "judgments.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_runs",
            "--config",
            "cfg.yaml",
            "--runs-dir",
            str(runs_dir),
            "--cases-dir",
            str(tmp_path / "cases"),
            "--judge-model",
            "judge_model",
            "--judge-id",
            "judge_v1",
            "--judge-prompt-version",
            "rubric_v1",
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    lines = out_jsonl.read_text().splitlines()
    assert len(lines) == 1
    judgment = json.loads(lines[0])
    assert judgment["schema_version"] == "athos.judgment.v1"
    assert judgment["run_id"] == "run-1"
    assert judgment["judge_id"] == "judge_v1"
    assert judgment["judge_model"] == "judge_model"
    assert judgment["judge_prompt_version"] == "rubric_v1"
    assert judgment["judgment_status"] == "scored"
    assert judgment["score"] == 88.0
    assert judgment["pass"] is True
    assert judgment["rationale"] == "good"


def test_score_runs_rescoring_to_separate_outputs(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text="response text",
    )

    case_root = tmp_path / "cases" / "case_one"
    case_root.mkdir(parents=True)
    (case_root / "user_description.txt").write_text("desc")
    (case_root / "solution.md").write_text("expected answer")

    dummy_cfg = SimpleNamespace(
        models={
            "judge_a": SimpleNamespace(model_id="judge_a"),
            "judge_b": SimpleNamespace(model_id="judge_b"),
        }
    )
    monkeypatch.setattr(score_runs_mod, "build_config", Mock(return_value=dummy_cfg))
    monkeypatch.setattr(
        score_runs_mod.smolagents_factories,
        "build_model",
        lambda _cfg: object(),
    )
    monkeypatch.setattr(
        score_runs_mod,
        "evaluate_response",
        lambda _model, _sol, _resp: (91, "ok"),
    )

    out_a = tmp_path / "judgments_a.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_runs",
            "--config",
            "cfg.yaml",
            "--runs-dir",
            str(runs_dir),
            "--cases-dir",
            str(tmp_path / "cases"),
            "--judge-model",
            "judge_a",
            "--judge-id",
            "judge_a_v1",
            "--judge-prompt-version",
            "rubric_v1",
            "--output",
            str(out_a),
        ],
    )
    score_runs_mod.main()

    out_b = tmp_path / "judgments_b.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_runs",
            "--config",
            "cfg.yaml",
            "--runs-dir",
            str(runs_dir),
            "--cases-dir",
            str(tmp_path / "cases"),
            "--judge-model",
            "judge_b",
            "--judge-id",
            "judge_b_v2",
            "--judge-prompt-version",
            "rubric_v2",
            "--output",
            str(out_b),
        ],
    )
    score_runs_mod.main()

    payload_a = json.loads(out_a.read_text().splitlines()[0])
    payload_b = json.loads(out_b.read_text().splitlines()[0])
    assert payload_a["run_id"] == payload_b["run_id"] == "run-1"
    assert payload_a["judge_id"] == "judge_a_v1"
    assert payload_a["judge_model"] == "judge_a"
    assert payload_a["judge_prompt_version"] == "rubric_v1"
    assert payload_b["judge_id"] == "judge_b_v2"
    assert payload_b["judge_model"] == "judge_b"
    assert payload_b["judge_prompt_version"] == "rubric_v2"
    assert payload_a["judgment_status"] == "scored"
    assert payload_b["judgment_status"] == "scored"


def test_score_runs_records_skips_and_fail_on_skip(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text="",
    )

    case_root = tmp_path / "cases" / "case_one"
    case_root.mkdir(parents=True)
    (case_root / "user_description.txt").write_text("desc")
    (case_root / "solution.md").write_text("expected answer")

    dummy_cfg = SimpleNamespace(
        models={"judge_model": SimpleNamespace(model_id="judge_model")}
    )
    monkeypatch.setattr(score_runs_mod, "build_config", Mock(return_value=dummy_cfg))
    monkeypatch.setattr(
        score_runs_mod.smolagents_factories,
        "build_model",
        lambda _cfg: object(),
    )
    monkeypatch.setattr(
        score_runs_mod,
        "evaluate_response",
        lambda _model, _sol, _resp: (88, "good"),
    )

    out_jsonl = tmp_path / "judgments.jsonl"
    skips_jsonl = tmp_path / "skips.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_runs",
            "--config",
            "cfg.yaml",
            "--runs-dir",
            str(runs_dir),
            "--cases-dir",
            str(tmp_path / "cases"),
            "--judge-model",
            "judge_model",
            "--judge-id",
            "judge_v1",
            "--judge-prompt-version",
            "rubric_v1",
            "--skips-output",
            str(skips_jsonl),
            "--fail-on-skip",
            "--output",
            str(out_jsonl),
        ],
    )
    with pytest.raises(SystemExit, match="fail-on-skip enabled"):
        score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_missing_output"
    assert judgment["score"] is None
    assert judgment["pass"] is None

    skip = json.loads(skips_jsonl.read_text().splitlines()[0])
    assert skip["schema_version"] == "athos.skip.v1"
    assert skip["run_id"] == "run-1"
    assert skip["reason"] == "skipped_missing_output"
