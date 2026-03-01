import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location(
    "filter_tickets_corpus_mod",
    REPO_ROOT / "scripts" / "filter_tickets_corpus.py",
)
filter_tickets_corpus_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filter_tickets_corpus_mod)


def _payload(*, incident_number: str, contact_type: str, local_paths: list[str]) -> dict[str, object]:
    return {
        "metadata": {"incident_number": incident_number, "sys_id": f"sys_{incident_number}"},
        "incident_fields": {
            "sys_created_on": "2025-01-01 00:00:00",
            "contact_type": contact_type,
            "short_description": "test",
            "description": "test",
        },
        "discussions": {"customer_facing_comments": [], "internal_work_notes": []},
        "attachments": [{"local_path": path} for path in local_paths],
    }


def test_filter_copies_selected_json_and_attachments(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"

    selected_json = incident_dir / "selected.json"
    selected_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0001",
                contact_type="Email",
                local_paths=["servicenow_incidents/INC001/01/example.log"],
            )
        ),
        encoding="utf-8",
    )
    filtered_json = incident_dir / "filtered_out.json"
    filtered_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0002",
                contact_type="Staff Initiated",
                local_paths=[],
            )
        ),
        encoding="utf-8",
    )

    referenced_attachment = incident_dir / "example.log"
    referenced_attachment.write_text("ref", encoding="utf-8")
    sibling_attachment_dir = incident_dir / "00_20260212_012659_attachements"
    sibling_attachment_dir.mkdir()
    sibling_attachment = sibling_attachment_dir / "extra.txt"
    sibling_attachment.write_text("sibling", encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "filter_tickets_corpus.py",
            str(source_root),
            "--output-root",
            str(output_root),
            "--manifest-out",
            str(manifest_path),
        ],
    )

    filter_tickets_corpus_mod.main()

    assert (output_root / "INC001" / "01" / "selected.json").exists()
    assert (output_root / "INC001" / "01" / "example.log").exists()
    assert (output_root / "INC001" / "01" / "00_20260212_012659_attachements" / "extra.txt").exists()
    assert not (output_root / "INC001" / "01" / "filtered_out.json").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["selected_files"] == 1
    assert manifest["counts"]["attachments_copied"] == 2
    assert manifest["counts"]["attachments_missing"] == 0
    assert manifest["source_path"] == str(output_root.resolve())
    assert manifest["upstream_source_path"] == str(source_root.resolve())


def test_filter_fails_on_missing_attachment_by_default(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    incident_json = incident_dir / "selected.json"
    incident_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0001",
                contact_type="Email",
                local_paths=["servicenow_incidents/INC001/01/missing.log"],
            )
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "filter_tickets_corpus.py",
            str(source_root),
            "--output-root",
            str(output_root),
            "--manifest-out",
            str(manifest_path),
        ],
    )

    with pytest.raises(RuntimeError, match="missing attachment references"):
        filter_tickets_corpus_mod.main()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["attachments_missing"] == 1


def test_filter_allows_missing_attachment_with_flag(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    incident_json = incident_dir / "selected.json"
    incident_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0001",
                contact_type="Email",
                local_paths=["servicenow_incidents/INC001/01/missing.log"],
            )
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "filter_tickets_corpus.py",
            str(source_root),
            "--output-root",
            str(output_root),
            "--manifest-out",
            str(manifest_path),
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["attachments_missing"] == 1
