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
