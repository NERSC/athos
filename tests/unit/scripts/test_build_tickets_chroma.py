import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location(
    "build_tickets_chroma_mod",
    REPO_ROOT / "scripts" / "build_tickets_chroma.py",
)
build_tickets_chroma_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_tickets_chroma_mod)


def _valid_ticket_payload() -> dict[str, object]:
    return {
        "metadata": {"incident_number": "INC0001", "sys_id": "sys_inc_1"},
        "incident_fields": {
            "sys_created_on": "2025-01-01 00:00:00",
            "contact_type": "Email",
            "short_description": "valid ticket",
            "description": "description",
        },
        "discussions": {"customer_facing_comments": [], "internal_work_notes": []},
        "attachments": [],
    }


def test_main_dry_run_fails_when_any_file_errors(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    source_root.mkdir()
    (source_root / "good.json").write_text(
        json.dumps(_valid_ticket_payload()),
        encoding="utf-8",
    )
    (source_root / "bad.json").write_text("{not valid json", encoding="utf-8")
    selected_manifest = tmp_path / "selected_manifest.json"
    selected_manifest.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["good.json", "bad.json"],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--dry-run",
        ],
    )

    with pytest.raises(RuntimeError, match="Encountered 1 file processing errors"):
        build_tickets_chroma_mod.main()


def test_main_dry_run_allows_file_errors_with_flag(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    source_root.mkdir()
    (source_root / "good.json").write_text(
        json.dumps(_valid_ticket_payload()),
        encoding="utf-8",
    )
    (source_root / "bad.json").write_text("{not valid json", encoding="utf-8")
    selected_manifest = tmp_path / "selected_manifest.json"
    selected_manifest.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["good.json", "bad.json"],
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--dry-run",
            "--allow-file-errors",
            "--manifest-out",
            str(manifest_path),
        ],
    )

    build_tickets_chroma_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["errors"] == 1


def test_main_requires_selected_manifest_arg(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            "--dry-run",
        ],
    )
    with pytest.raises(SystemExit):
        build_tickets_chroma_mod.main()


def test_main_dry_run_ingests_from_selected_manifest_without_refiltering(
    tmp_path: Path, monkeypatch
):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    ticket_path = incident_dir / "selected.json"
    ticket_path.write_text(
        json.dumps(
            {
                "metadata": {"incident_number": "INC0001", "sys_id": "sys_inc_1"},
                "incident_fields": {
                    "sys_created_on": "2019-01-01 00:00:00",
                    "contact_type": "Staff Initiated",
                    "short_description": "old auto-generated incident",
                    "description": "old incident",
                },
                "discussions": {"customer_facing_comments": [], "internal_work_notes": []},
                "attachments": [],
            }
        ),
        encoding="utf-8",
    )
    selected_manifest = tmp_path / "selected_manifest.json"
    selected_manifest.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["INC001/01/selected.json"],
            }
        ),
        encoding="utf-8",
    )
    ingest_manifest = tmp_path / "ingest_manifest.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--dry-run",
            "--manifest-out",
            str(ingest_manifest),
        ],
    )

    build_tickets_chroma_mod.main()
    manifest = json.loads(ingest_manifest.read_text(encoding="utf-8"))
    assert manifest["input_source_mode"] == "selected_corpus_manifest"
    assert manifest["counts"]["kept_tickets"] == 1
    assert "filtered" not in manifest["counts"]


def test_main_non_dry_run_fails_before_writing_when_file_errors(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    source_root.mkdir()
    (source_root / "good.json").write_text(
        json.dumps(_valid_ticket_payload()),
        encoding="utf-8",
    )
    (source_root / "bad.json").write_text("{not valid json", encoding="utf-8")
    selected_manifest = tmp_path / "selected_manifest.json"
    selected_manifest.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": ["good.json", "bad.json"],
            }
        ),
        encoding="utf-8",
    )
    persist_dir = tmp_path / "chroma"
    ingest_manifest = tmp_path / "ingest_manifest.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--persist-dir",
            str(persist_dir),
            "--collection-name",
            "ticket_ingest_atomicity_test",
            "--manifest-out",
            str(ingest_manifest),
        ],
    )

    with pytest.raises(RuntimeError, match="Encountered 1 file processing errors"):
        build_tickets_chroma_mod.main()

    assert ingest_manifest.exists()
    loaded = json.loads(ingest_manifest.read_text(encoding="utf-8"))
    assert loaded["counts"]["errors"] == 1
    # Pre-write failure should avoid creating Chroma persistence artifacts.
    assert not persist_dir.exists()


def test_main_rejects_non_materialized_selected_manifest(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    source_root.mkdir()
    selected_manifest = tmp_path / "selected_manifest.json"
    selected_manifest.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(tmp_path / "filtered"),
                "selected_files": ["INC001/01/selected.json"],
                "config": {"dry_run": True, "materialized": False},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--dry-run",
        ],
    )

    with pytest.raises(ValueError, match="non-materialized output"):
        build_tickets_chroma_mod.main()


def test_main_dry_run_ingests_from_derived_jsonl(tmp_path: Path, monkeypatch):
    derived_jsonl = tmp_path / "derived.jsonl"
    derived_jsonl.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "incident_number": "INC0196020",
                        "sys_id": "abc123",
                        "sys_created_on": "2023-01-02 03:30:18",
                        "state": "Closed",
                        "close_code": "Solved (Permanently)",
                        "category": "Programming",
                        "subcategory": "C/C++",
                        "assignment_group": "Consulting",
                        "incident_summary": "Compile failed after loading a broken GSL module.",
                        "resolution_summary": "Support fixed the modulefile.",
                        "retrieval_keywords": ["gsl", "module load error"],
                        "evidence_snippets": [
                            "fatal error: gsl/gsl_sf.h: No such file or directory"
                        ],
                        "schema_version": "athos.derived_ticket_record.v2",
                        "source_json_path": "/tmp/INC0196020.json",
                    }
                )
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "ingest_manifest.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            "--derived-jsonl",
            str(derived_jsonl),
            "--dry-run",
            "--manifest-out",
            str(manifest_path),
        ],
    )

    build_tickets_chroma_mod.main()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["input_source_mode"] == "derived_jsonl"
    assert manifest["derived_jsonl"] == str(derived_jsonl.resolve())
    assert manifest["counts"]["input_records"] == 1
    assert manifest["counts"]["documents_written"] == 1
