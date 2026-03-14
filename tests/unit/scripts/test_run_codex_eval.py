import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

spec = importlib.util.spec_from_file_location(
    "run_codex_eval_mod",
    REPO_ROOT / "scripts" / "run_codex_eval.py",
)
run_codex_eval_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_codex_eval_mod)


def test_build_prompt_includes_bundle_root():
    prompt = run_codex_eval_mod._build_prompt(
        dataset_id="simple_qa",
        case_id="perlmutter_debug_qos",
        case_input="What is the Perlmutter debug QOS time limit?",
        bundle_root=Path("/tmp/file_retrieval_corpus"),
    )
    assert "/tmp/file_retrieval_corpus/INDEX.md" in prompt
    assert "perlmutter_debug_qos" in prompt


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

    bundle_root = tmp_path / "file_retrieval_corpus"
    bundle_root.mkdir(parents=True)
    (bundle_root / "INDEX.md").write_text("start here")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_codex_eval.py",
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

    run_codex_eval_mod.main()
    out = capsys.readouterr().out.strip().splitlines()
    assert "test_cases/sbatch-qos-error" in out
