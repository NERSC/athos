import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

spec = importlib.util.spec_from_file_location(
    "run_claude_code_eval_mod",
    REPO_ROOT / "scripts" / "run_claude_code_eval.py",
)
run_claude_code_eval_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_claude_code_eval_mod)


def test_extract_answer_and_sidecar_from_json_result():
    answer, sidecar = run_claude_code_eval_mod._extract_answer_and_sidecar(
        {
            "result": json.dumps(
                {
                    "answer": "Use regular QOS for an 8 hour job.",
                    "citations": ["workspace/file_retrieval_corpus/docs/jobs/policy.md"],
                    "notes": "debug has a 30 minute limit",
                }
            )
        }
    )
    assert answer == "Use regular QOS for an 8 hour job."
    assert sidecar["citations"] == ["workspace/file_retrieval_corpus/docs/jobs/policy.md"]


def test_extract_answer_and_sidecar_from_structured_output():
    answer, sidecar = run_claude_code_eval_mod._extract_answer_and_sidecar(
        {
            "result": "",
            "structured_output": {
                "answer": "Use regular QOS for an 8 hour job.",
                "citations": ["workspace/file_retrieval_corpus/docs/jobs/policy.md"],
                "notes": "debug has a 30 minute limit",
            },
        }
    )

    assert answer == "Use regular QOS for an 8 hour job."
    assert sidecar == {
        "citations": ["workspace/file_retrieval_corpus/docs/jobs/policy.md"],
        "notes": "debug has a 30 minute limit",
    }


def test_build_metrics_uses_claude_json_fields():
    metrics = run_claude_code_eval_mod._build_metrics(
        {
            "duration_ms": 1815,
            "duration_api_ms": 3083,
            "total_cost_usd": 0.06354125,
            "usage": {
                "input_tokens": 3,
                "output_tokens": 15,
                "cache_creation_input_tokens": 16719,
                "cache_read_input_tokens": 0,
            },
        }
    )
    assert metrics["latency_ms"] == 1815
    assert metrics["latency_api_ms"] == 3083
    assert metrics["cost_usd"] == 0.06354125
    assert metrics["token_usage"]["total_tokens"] == 16737


def test_dry_run_filters_cases(monkeypatch, tmp_path, capsys):
    qa_file = tmp_path / "simple_qa.jsonl"
    qa_file.write_text(
        json.dumps(
            {
                "id": "perlmutter_debug_qos",
                "question": "What is the debug QOS time limit?",
                "answer": "30 minutes",
            }
        )
        + "\n"
    )
    cases_dir = tmp_path / "test_cases"
    case_dir = cases_dir / "sbatch-qos-error"
    files_dir = case_dir / "files"
    files_dir.mkdir(parents=True)
    (case_dir / "user_description.txt").write_text("job submit fails")
    (case_dir / "solution.md").write_text("use regular qos")
    (files_dir / "job.sh").write_text("#SBATCH -q debug")

    bundle_root = tmp_path / "workspace" / "file_retrieval_corpus"
    bundle_root.mkdir(parents=True)
    (bundle_root / "INDEX.md").write_text("start here")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_claude_code_eval.py",
            "--qa-file",
            str(qa_file),
            "--cases-dir",
            str(cases_dir),
            "--bundle-root",
            str(bundle_root),
            "--case-id",
            "sbatch-qos-error",
            "--dry-run",
        ],
    )

    run_claude_code_eval_mod.main()
    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["test_cases/sbatch-qos-error"]
    assert "Loaded QA dataset" in captured.err
