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


def _write_run(
    path: Path,
    run_id: str,
    case_id: str,
    output_text: str,
    dataset_id: str = "cases",
    execution_status: str = "success",
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    payload = {
        "schema_version": "athos.run.v1",
        "run_id": run_id,
        "experiment_id": "exp1",
        "dataset_id": dataset_id,
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
            "status": execution_status,
            "error_type": error_type,
            "error_message": error_message,
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
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
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
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
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
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
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
    assert judgment["score"] == 0.0
    assert judgment["pass"] is False

    skip = json.loads(skips_jsonl.read_text().splitlines()[0])
    assert skip["schema_version"] == "athos.skip.v1"
    assert skip["run_id"] == "run-1"
    assert skip["reason"] == "skipped_missing_output"


def test_score_runs_skip_details_not_written_without_skips_output(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_missing_output"
    assert not any(tmp_path.glob("*.skips.jsonl"))


def test_score_runs_treats_whitespace_output_as_missing(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text="   ",
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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_missing_output"
    assert judgment["score"] == 0.0
    assert judgment["pass"] is False


def test_score_runs_resolves_references_by_dataset_and_case_id(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "ds1" / "shared_case" / "0" / "run.json",
        run_id="run-1",
        case_id="shared_case",
        output_text="response text",
        dataset_id="ds1",
    )

    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "ds2" / "shared_case" / "0" / "run.json",
        run_id="run-2",
        case_id="shared_case",
        output_text="response text",
        dataset_id="ds2",
    )

    ds1_root = tmp_path / "ds1" / "shared_case"
    ds1_root.mkdir(parents=True)
    (ds1_root / "user_description.txt").write_text("desc")
    (ds1_root / "solution.md").write_text("solution one")

    ds2_root = tmp_path / "ds2" / "shared_case"
    ds2_root.mkdir(parents=True)
    (ds2_root / "user_description.txt").write_text("desc")
    (ds2_root / "solution.md").write_text("solution two")

    dummy_cfg = SimpleNamespace(
        models={"judge_model": SimpleNamespace(model_id="judge_model")}
    )
    monkeypatch.setattr(score_runs_mod, "build_config", Mock(return_value=dummy_cfg))
    monkeypatch.setattr(
        score_runs_mod.smolagents_factories,
        "build_model",
        lambda _cfg: object(),
    )

    seen_references = []

    def _record_reference(_model, reference, _resp):
        seen_references.append(reference)
        return 90, "ok"

    monkeypatch.setattr(score_runs_mod, "evaluate_response", _record_reference)

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
            str(tmp_path / "ds1"),
            "--cases-dir",
            str(tmp_path / "ds2"),
            "--judge-model",
            "judge_model",
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    assert sorted(seen_references) == ["solution one", "solution two"]


def test_score_runs_emits_skipped_judgment_when_run_id_missing(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    run_path = runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json"
    payload = {
        "schema_version": "athos.run.v1",
        "experiment_id": "exp1",
        "dataset_id": "cases",
        "case_id": "case_one",
        "run_index": 0,
        "agent_system": "athos",
        "config_id": "cfg",
        "execution": {"status": "success"},
        "response": {"output_text": "response"},
    }
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text(json.dumps(payload))

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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_invalid_run"
    assert judgment["run_id"].startswith("missing_run_id:")
    assert judgment["run_path"] == str(run_path.resolve())


def test_score_runs_skips_non_success_execution_status(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    run_path = runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json"
    payload = {
        "schema_version": "athos.run.v1",
        "run_id": "run-1",
        "experiment_id": "exp1",
        "dataset_id": "cases",
        "case_id": "case_one",
        "run_index": 0,
        "agent_system": "athos",
        "config_id": "cfg",
        "execution": {"status": "execution_error"},
        "response": {"output_text": "diagnostic text"},
    }
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text(json.dumps(payload))

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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_execution_status"
    assert judgment["score"] == 0.0
    assert judgment["pass"] is False


def test_score_runs_skips_upstream_error_status(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text="Error: Error code: 504 - gateway failure",
        execution_status="upstream_error",
        error_type="http_504",
        error_message="Upstream gateway/provider failure in flow output.",
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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_upstream_error"
    assert judgment["score"] == 0.0
    assert judgment["pass"] is False


def test_score_runs_legacy_error_output_detects_gateway_time_out(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text=(
            "Error: Error code: 504 - <html><h1>504 Gateway Time-out</h1></html>"
        ),
        execution_status="success",
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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_upstream_error"
    assert judgment["score"] == 0.0
    assert judgment["pass"] is False


def test_score_runs_does_not_skip_normal_answer_that_mentions_bad_gateway(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text=(
            "The service returned 502 Bad Gateway earlier, but the likely issue is"
            " backend overload. Retry after maintenance."
        ),
        execution_status="success",
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
        lambda _model, _sol, _resp: (91, "good"),
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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "scored"
    assert judgment["score"] == 91.0
    assert judgment["pass"] is True


def test_score_runs_does_not_skip_successful_json_with_error_field(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
        run_id="run-1",
        case_id="case_one",
        output_text=(
            '{"summary":"incident analysis","error":"saw prior 503 Service Unavailable",'
            '"next_step":"retry and verify"}'
        ),
        execution_status="success",
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
        lambda _model, _sol, _resp: (89, "good"),
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
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "scored"
    assert judgment["score"] == 89.0
    assert judgment["pass"] is True


def test_score_runs_retries_then_skips_non_numeric_judge_score(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
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
    evaluate_response = Mock(
        return_value=("not-a-number", "judge returned malformed output")
    )
    monkeypatch.setattr(score_runs_mod, "evaluate_response", evaluate_response)

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
            "--judge-max-attempts",
            "3",
            "--skips-output",
            str(skips_jsonl),
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    assert evaluate_response.call_count == 3
    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "skipped_judge_error"
    assert judgment["score"] == 0.0
    assert judgment["pass"] is False
    assert "non_numeric_score='not-a-number'" in judgment["rationale"]

    skip = json.loads(skips_jsonl.read_text().splitlines()[0])
    assert skip["reason"] == "skipped_judge_error"
    assert "non_numeric_score='not-a-number'" in skip["detail"]


def test_score_runs_recovers_after_non_numeric_judge_score(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    _write_run(
        runs_dir / "exp1" / "athos" / "cfg" / "cases" / "case_one" / "0" / "run.json",
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
    evaluate_response = Mock(
        side_effect=[
            ("not-a-number", "judge returned malformed output"),
            (87, "judge recovered"),
        ]
    )
    monkeypatch.setattr(score_runs_mod, "evaluate_response", evaluate_response)

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
            "--judge-max-attempts",
            "3",
            "--output",
            str(out_jsonl),
        ],
    )
    score_runs_mod.main()

    assert evaluate_response.call_count == 2
    judgment = json.loads(out_jsonl.read_text().splitlines()[0])
    assert judgment["judgment_status"] == "scored"
    assert judgment["score"] == 87.0
    assert judgment["pass"] is True
    assert judgment["rationale"] == "judge recovered"
