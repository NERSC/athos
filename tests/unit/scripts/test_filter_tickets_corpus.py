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


def _payload(
    *,
    incident_number: str,
    contact_type: str,
    local_paths: list[str],
    close_code: str = "Solved (Permanently)",
) -> dict[str, object]:
    return {
        "metadata": {"incident_number": incident_number, "sys_id": f"sys_{incident_number}"},
        "incident_fields": {
            "sys_created_on": "2025-01-01 00:00:00",
            "contact_type": contact_type,
            "close_code": close_code,
            "state": "Closed",
            "short_description": "test",
            "description": "test",
        },
        "discussions": {
            "customer_facing_comments": [
                {"timestamp": "2025-01-01 00:00:00", "created_by": "user", "text": "help"}
            ],
            "internal_work_notes": [],
        },
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
    sibling_attachment_dir = incident_dir / "selected_20260212_012659_attachements"
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
    assert (output_root / "INC001" / "01" / "selected_20260212_012659_attachements" / "extra.txt").exists()
    assert not (output_root / "INC001" / "01" / "filtered_out.json").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["selected_files"] == 1
    assert manifest["counts"]["attachments_copied"] == 2
    assert manifest["counts"]["attachments_missing"] == 0
    assert manifest["source_path"] == str(output_root.resolve())
    assert manifest["upstream_source_path"] == str(source_root.resolve())
    assert manifest["config"]["materialized"] is True


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
            "--no-exclude-if-single-message-no-attachments",
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["attachments_missing"] == 1


def test_filter_dry_run_marks_manifest_non_materialized(tmp_path: Path, monkeypatch):
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
                local_paths=[],
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
            "--dry-run",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["config"]["dry_run"] is True
    assert manifest["config"]["materialized"] is False


def test_filter_rejects_out_of_root_attachment_paths(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("secret", encoding="utf-8")
    escaped_rel = "../secret.txt"

    incident_json = incident_dir / "selected.json"
    incident_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0001",
                contact_type="Email",
                local_paths=[str(secret_file), escaped_rel],
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
            "--no-exclude-if-single-message-no-attachments",
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()

    assert (output_root / "INC001" / "01" / "selected.json").exists()
    assert not (output_root / "secret.txt").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["attachments_missing"] == 2


def test_filter_balanced_default_excludes_short_description_pattern(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    incident_json = incident_dir / "selected.json"
    incident_json.write_text(
        json.dumps(
            {
                "metadata": {"incident_number": "INC0001", "sys_id": "sys_inc_1"},
                "incident_fields": {
                    "sys_created_on": "2025-01-01 00:00:00",
                    "contact_type": "Email",
                    "close_code": "Solved (Permanently)",
                    "state": "Closed",
                    "short_description": "Storage Quota Increase Request: project",
                    "description": "request",
                },
                "discussions": {"customer_facing_comments": [], "internal_work_notes": []},
                "attachments": [],
            }
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
            "--no-exclude-if-single-message-no-attachments",
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["selected_files"] == 0
    assert manifest["counts"]["filtered_by_reason"]["excluded_short_description_prefix"] == 1


def test_filter_ignores_non_matching_sibling_attachment_dirs(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    incident_json = incident_dir / "94.json"
    incident_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0001",
                contact_type="Email",
                local_paths=[],
            )
        ),
        encoding="utf-8",
    )

    unrelated_attachment_dir = incident_dir / "36_20260212_012659_attachements"
    unrelated_attachment_dir.mkdir()
    unrelated_attachment = unrelated_attachment_dir / "extra.txt"
    unrelated_attachment.write_text("sibling", encoding="utf-8")

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
            "--no-exclude-if-single-message-no-attachments",
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["selected_files"] == 1
    assert manifest["counts"]["attachments_copied"] == 0
    assert not (output_root / "INC001" / "01" / "36_20260212_012659_attachements" / "extra.txt").exists()


def test_filter_balanced_default_requires_solved_permanently(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    rejected_json = incident_dir / "rejected.json"
    rejected_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0001",
                contact_type="Email",
                local_paths=[],
                close_code="Not Solved (No User Response)",
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
            "--no-exclude-if-single-message-no-attachments",
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["selected_files"] == 0
    assert manifest["counts"]["filtered_by_reason"]["close_code_not_in_include_list"] == 1
    assert manifest["config"]["include_close_codes"] == ["Solved (Permanently)"]


def test_filter_allows_overriding_include_close_code(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    selected_json = incident_dir / "selected.json"
    selected_json.write_text(
        json.dumps(
            _payload(
                incident_number="INC0001",
                contact_type="Email",
                local_paths=[],
                close_code="Not Solved (No User Response)",
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
            "--include-close-code",
            "Not Solved (No User Response)",
            "--no-exclude-if-single-message-no-attachments",
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["selected_files"] == 1
    assert manifest["config"]["include_close_codes"] == ["Not Solved (No User Response)"]


def test_filter_excludes_non_closed_state_even_with_solved_close_code(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    output_root = tmp_path / "filtered"
    manifest_path = tmp_path / "manifest.json"

    payload = _payload(
        incident_number="INC0003",
        contact_type="Email",
        local_paths=[],
        close_code="Solved (Permanently)",
    )
    payload["incident_fields"]["state"] = "Awaiting Vendor"

    incident_json = incident_dir / "selected.json"
    incident_json.write_text(json.dumps(payload), encoding="utf-8")

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
            "--no-exclude-if-single-message-no-attachments",
            "--allow-missing-attachments",
        ],
    )

    filter_tickets_corpus_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["selected_files"] == 0
    assert manifest["counts"]["filtered_by_reason"]["state_not_closed_or_resolved"] == 1
