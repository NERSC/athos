import importlib.util
import json
import sys
from pathlib import Path

import pytest

from athos.config.models import AthosConfig, ModelConfig


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location(
    "build_derived_ticket_corpus_mod",
    REPO_ROOT / "scripts" / "build_derived_ticket_corpus.py",
)
build_derived_ticket_corpus_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_derived_ticket_corpus_mod)


def _record() -> dict:
    return {
        "metadata": {"incident_number": "INC0001", "sys_id": "sys_inc_1"},
        "incident_fields": {
            "sys_created_on": "2025-01-01 00:00:00",
            "state": "Closed",
            "close_code": "Solved (Permanently)",
            "category": "Software",
            "subcategory": "Python",
            "assignment_group": "Consulting",
            "short_description": "numpy import fails",
            "description": "",
        },
        "discussions": {
            "customer_facing_comments": [
                {"timestamp": "2025-01-01 00:00:00", "created_by": "USER_A", "text": "import failed"}
            ],
            "internal_work_notes": [],
        },
        "attachments": [],
    }


def _athos_config() -> AthosConfig:
    return AthosConfig(
        workspace_dir="/tmp/athos_workspace",
        models={
            "cborg_coder": ModelConfig(
                model_id="lbl/cborg-coder",
                temperature=0.3,
                max_tokens=4096,
            )
        },
        tools={},
        mcp_servers={},
        flows={},
    )


def test_build_derived_ticket_corpus_success_and_retry(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "filtered"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    ticket_path = incident_dir / "ticket.json"
    ticket_path.write_text(json.dumps(_record()), encoding="utf-8")
    manifest_path = tmp_path / "selected_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["INC001/01/ticket.json"],
            }
        ),
        encoding="utf-8",
    )
    output_jsonl = tmp_path / "derived.jsonl"

    responses = iter(
        [
            '{"incident_summary":"bad","resolution_summary":"","retrieval_keywords":[],"evidence_snippets":[]}',
            '{"incident_summary":"numpy import failed because the environment was missing a module path.","resolution_summary":"rebuilt environment","retrieval_keywords":["numpy","import error"],"evidence_snippets":["ModuleNotFoundError"]}',
        ]
    )

    monkeypatch.setattr(
        build_derived_ticket_corpus_mod.ConfigLoader,
        "load_config",
        staticmethod(lambda _: _athos_config()),
    )
    monkeypatch.setattr(build_derived_ticket_corpus_mod, "_build_openai_client", lambda _: object())
    monkeypatch.setattr(
        build_derived_ticket_corpus_mod,
        "_invoke_model_json",
        lambda client, model_cfg, prompt: next(responses),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_derived_ticket_corpus.py",
            "--selected-corpus-manifest",
            str(manifest_path),
            "--output-jsonl",
            str(output_jsonl),
            "--allow-transform-errors",
        ],
    )

    build_derived_ticket_corpus_mod.main()

    lines = output_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["incident_number"] == "INC0001"
    assert "retrieval_document" not in record
    assert record["provenance"]["validation_attempts"] == 2

    derived_manifest = json.loads(
        output_jsonl.with_suffix(output_jsonl.suffix + ".manifest.json").read_text(encoding="utf-8")
    )
    assert derived_manifest["counts"]["successful_records"] == 1
    assert derived_manifest["counts"]["transform_retries"] == 1
    assert derived_manifest["counts"]["failed_records"] == 0


def test_build_derived_ticket_corpus_raises_on_transform_failure(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "filtered"
    source_root.mkdir()
    ticket_path = source_root / "ticket.json"
    ticket_path.write_text(json.dumps(_record()), encoding="utf-8")
    manifest_path = tmp_path / "selected_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["ticket.json"],
            }
        ),
        encoding="utf-8",
    )
    output_jsonl = tmp_path / "derived.jsonl"

    monkeypatch.setattr(
        build_derived_ticket_corpus_mod.ConfigLoader,
        "load_config",
        staticmethod(lambda _: _athos_config()),
    )
    monkeypatch.setattr(build_derived_ticket_corpus_mod, "_build_openai_client", lambda _: object())
    monkeypatch.setattr(
        build_derived_ticket_corpus_mod,
        "_invoke_model_json",
        lambda client, model_cfg, prompt: '{"incident_summary":"","resolution_summary":"","retrieval_keywords":[],"evidence_snippets":[]}',
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_derived_ticket_corpus.py",
            "--selected-corpus-manifest",
            str(manifest_path),
            "--output-jsonl",
            str(output_jsonl),
            "--max-retries",
            "1",
        ],
    )

    with pytest.raises(RuntimeError, match="derived transform failures"):
        build_derived_ticket_corpus_mod.main()

    failures_path = output_jsonl.with_suffix(output_jsonl.suffix + ".failures.jsonl")
    failure_lines = failures_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(failure_lines) == 1
    failure = json.loads(failure_lines[0])
    assert failure["stage"] == "transform"

    derived_manifest = json.loads(
        output_jsonl.with_suffix(output_jsonl.suffix + ".manifest.json").read_text(encoding="utf-8")
    )
    assert derived_manifest["counts"]["successful_records"] == 0
    assert derived_manifest["counts"]["failed_records"] == 1
    assert derived_manifest["counts"]["transform_failures"] == 1
    review_path = output_jsonl.with_suffix(output_jsonl.suffix + ".review.jsonl")
    review_lines = review_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(review_lines) == 1
    review = json.loads(review_lines[0])
    assert review["stage"] == "transform"
    assert review["last_raw_response"] is not None
    assert review["violations"]


def test_build_derived_ticket_corpus_materializes_markdown_files(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "filtered"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    ticket_path = incident_dir / "ticket.json"
    ticket_path.write_text(json.dumps(_record()), encoding="utf-8")
    manifest_path = tmp_path / "selected_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["INC001/01/ticket.json"],
            }
        ),
        encoding="utf-8",
    )
    output_jsonl = tmp_path / "derived.jsonl"
    materialize_dir = tmp_path / "materialized"

    monkeypatch.setattr(
        build_derived_ticket_corpus_mod.ConfigLoader,
        "load_config",
        staticmethod(lambda _: _athos_config()),
    )
    monkeypatch.setattr(build_derived_ticket_corpus_mod, "_build_openai_client", lambda _: object())
    monkeypatch.setattr(
        build_derived_ticket_corpus_mod,
        "_invoke_model_json",
        lambda client, model_cfg, prompt: (
            '{"incident_summary":"numpy import failed in a Python environment.",'
            '"resolution_summary":"Support rebuilt the environment.",'
            '"retrieval_keywords":["numpy","import error"],'
            '"evidence_snippets":["ModuleNotFoundError"]}'
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_derived_ticket_corpus.py",
            "--selected-corpus-manifest",
            str(manifest_path),
            "--output-jsonl",
            str(output_jsonl),
            "--materialize-dir",
            str(materialize_dir),
            "--allow-transform-errors",
        ],
    )

    build_derived_ticket_corpus_mod.main()

    materialized_file = materialize_dir / "INC000" / "1" / ".md"
    assert not materialized_file.exists()
    materialized_files = sorted(materialize_dir.rglob("*.md"))
    assert len(materialized_files) == 2
    ticket_markdown = next(path for path in materialized_files if path.name != "INDEX.md")
    assert "# INC0001" in ticket_markdown.read_text(encoding="utf-8")
    materialized_manifest = json.loads(
        (materialize_dir / "manifest.json").read_text(encoding="utf-8")
    )
    assert materialized_manifest["record_count"] == 1


def test_build_derived_ticket_corpus_resume_skips_existing_records(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "filtered"
    source_root.mkdir()
    ticket_path = source_root / "ticket.json"
    ticket_path.write_text(json.dumps(_record()), encoding="utf-8")
    manifest_path = tmp_path / "selected_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["ticket.json"],
            }
        ),
        encoding="utf-8",
    )
    output_jsonl = tmp_path / "derived.jsonl"
    output_jsonl.write_text(
        json.dumps({"incident_number": "INC0001", "incident_summary": "existing"}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        build_derived_ticket_corpus_mod.ConfigLoader,
        "load_config",
        staticmethod(lambda _: _athos_config()),
    )
    monkeypatch.setattr(build_derived_ticket_corpus_mod, "_build_openai_client", lambda _: object())
    called = {"count": 0}

    def _unexpected_call(client, model_cfg, prompt):
        called["count"] += 1
        raise AssertionError("transform should not be invoked for resumed existing record")

    monkeypatch.setattr(
        build_derived_ticket_corpus_mod,
        "_invoke_model_json",
        _unexpected_call,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_derived_ticket_corpus.py",
            "--selected-corpus-manifest",
            str(manifest_path),
            "--output-jsonl",
            str(output_jsonl),
            "--resume",
            "--allow-transform-errors",
        ],
    )

    build_derived_ticket_corpus_mod.main()

    assert called["count"] == 0
    lines = output_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    derived_manifest = json.loads(
        output_jsonl.with_suffix(output_jsonl.suffix + ".manifest.json").read_text(encoding="utf-8")
    )
    assert derived_manifest["counts"]["resumed_skipped"] == 1
    assert derived_manifest["counts"]["output_records_total"] == 1


def test_build_derived_ticket_corpus_materialized_manifest_counts_total_records_on_resume(
    tmp_path: Path, monkeypatch
):
    source_root = tmp_path / "filtered"
    source_root.mkdir()
    ticket_path = source_root / "ticket.json"
    ticket_path.write_text(json.dumps(_record()), encoding="utf-8")
    manifest_path = tmp_path / "selected_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["ticket.json"],
            }
        ),
        encoding="utf-8",
    )
    output_jsonl = tmp_path / "derived.jsonl"
    output_jsonl.write_text(
        json.dumps({"incident_number": "INC0001", "incident_summary": "existing"}) + "\n",
        encoding="utf-8",
    )
    materialize_dir = tmp_path / "materialized"
    existing_path = materialize_dir / "INC000" / "00" / "1.md"
    existing_path.parent.mkdir(parents=True)
    existing_path.write_text("# INC0001\n", encoding="utf-8")

    monkeypatch.setattr(
        build_derived_ticket_corpus_mod.ConfigLoader,
        "load_config",
        staticmethod(lambda _: _athos_config()),
    )
    monkeypatch.setattr(build_derived_ticket_corpus_mod, "_build_openai_client", lambda _: object())
    monkeypatch.setattr(
        build_derived_ticket_corpus_mod,
        "_invoke_model_json",
        lambda client, model_cfg, prompt: (_ for _ in ()).throw(
            AssertionError("transform should not be invoked for resumed existing record")
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_derived_ticket_corpus.py",
            "--selected-corpus-manifest",
            str(manifest_path),
            "--output-jsonl",
            str(output_jsonl),
            "--materialize-dir",
            str(materialize_dir),
            "--resume",
            "--allow-transform-errors",
        ],
    )

    build_derived_ticket_corpus_mod.main()

    materialized_manifest = json.loads(
        (materialize_dir / "manifest.json").read_text(encoding="utf-8")
    )
    assert materialized_manifest["record_count"] == 1
