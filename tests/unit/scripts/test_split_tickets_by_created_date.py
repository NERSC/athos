import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

spec = importlib.util.spec_from_file_location(
    "split_tickets_by_created_date_mod",
    REPO_ROOT / "scripts" / "split_tickets_by_created_date.py",
)
split_tickets_by_created_date_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(split_tickets_by_created_date_mod)


def _payload(*, incident_number: str, created_on: str | None, local_paths: list[str]) -> dict[str, object]:
    incident_fields: dict[str, object] = {
        "number": incident_number,
        "close_code": "Solved (Permanently)",
    }
    if created_on is not None:
        incident_fields["sys_created_on"] = created_on
    return {
        "metadata": {"incident_number": incident_number, "sys_id": f"sys_{incident_number}"},
        "incident_fields": incident_fields,
        "discussions": {
            "customer_facing_comments": [
                {"timestamp": "2026-01-01 00:00:00", "created_by": "user", "text": "help"}
            ],
            "internal_work_notes": [],
        },
        "attachments": [{"local_path": item} for item in local_paths],
    }


def test_split_dry_run_partitions_and_reports_counts(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "filtered"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)

    (incident_dir / "candidate.json").write_text(
        json.dumps(
            _payload(
                incident_number="INC1001",
                created_on="2026-01-15 10:00:00",
                local_paths=[],
            )
        ),
        encoding="utf-8",
    )
    (incident_dir / "retrieval.json").write_text(
        json.dumps(
            _payload(
                incident_number="INC1002",
                created_on="2025-12-20 10:00:00",
                local_paths=[],
            )
        ),
        encoding="utf-8",
    )
    (incident_dir / "missing_date.json").write_text(
        json.dumps(
            _payload(
                incident_number="INC1003",
                created_on=None,
                local_paths=[],
            )
        ),
        encoding="utf-8",
    )

    selected_manifest = tmp_path / "selected_manifest.json"
    selected_manifest.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": [
                    "INC001/01/candidate.json",
                    "INC001/01/retrieval.json",
                    "INC001/01/missing_date.json",
                ],
            }
        ),
        encoding="utf-8",
    )

    candidate_manifest = tmp_path / "candidate_manifest.json"
    retrieval_manifest = tmp_path / "retrieval_manifest.json"
    split_report = tmp_path / "split_report.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "split_tickets_by_created_date.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--cutoff-date",
            "2026-01-01",
            "--candidate-output-root",
            str(tmp_path / "candidate_root"),
            "--retrieval-output-root",
            str(tmp_path / "retrieval_root"),
            "--candidate-manifest-out",
            str(candidate_manifest),
            "--retrieval-manifest-out",
            str(retrieval_manifest),
            "--split-report-out",
            str(split_report),
            "--dry-run",
        ],
    )

    split_tickets_by_created_date_mod.main()

    candidate_obj = json.loads(candidate_manifest.read_text(encoding="utf-8"))
    retrieval_obj = json.loads(retrieval_manifest.read_text(encoding="utf-8"))
    report_obj = json.loads(split_report.read_text(encoding="utf-8"))

    assert candidate_obj["counts"]["selected_files"] == 1
    assert retrieval_obj["counts"]["selected_files"] == 1
    assert candidate_obj["counts"]["excluded_by_reason"]["missing_or_invalid_created_date"] == 1
    assert retrieval_obj["counts"]["excluded_by_reason"]["missing_or_invalid_created_date"] == 1
    assert report_obj["counts"]["candidate_files"] == 1
    assert report_obj["counts"]["retrieval_files"] == 1
    assert report_obj["counts"]["missing_or_invalid_created_date"] == 1
    assert report_obj["counts"]["incident_overlap"] == 0


def test_split_materializes_json_and_attachments(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "filtered"
    incident_dir = source_root / "INC010" / "99"
    incident_dir.mkdir(parents=True)

    attachment_path = incident_dir / "example.log"
    attachment_path.write_text("log", encoding="utf-8")

    sibling_attachment_dir = incident_dir / "candidate_20260212_012659_attachements"
    sibling_attachment_dir.mkdir()
    sibling_attachment = sibling_attachment_dir / "extra.txt"
    sibling_attachment.write_text("extra", encoding="utf-8")

    (incident_dir / "candidate.json").write_text(
        json.dumps(
            _payload(
                incident_number="INC9001",
                created_on="2026-02-10 11:00:00",
                local_paths=["INC010/99/example.log"],
            )
        ),
        encoding="utf-8",
    )
    (incident_dir / "retrieval.json").write_text(
        json.dumps(
            _payload(
                incident_number="INC9002",
                created_on="2025-05-01 11:00:00",
                local_paths=[],
            )
        ),
        encoding="utf-8",
    )

    selected_manifest = tmp_path / "selected_manifest.json"
    selected_manifest.write_text(
        json.dumps(
            {
                "schema_version": "athos.ticket_filter_manifest.v1",
                "source_path": str(source_root),
                "selected_files": [
                    "INC010/99/candidate.json",
                    "INC010/99/retrieval.json",
                ],
            }
        ),
        encoding="utf-8",
    )

    candidate_root = tmp_path / "candidate_root"
    retrieval_root = tmp_path / "retrieval_root"
    candidate_manifest = tmp_path / "candidate_manifest.json"
    retrieval_manifest = tmp_path / "retrieval_manifest.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "split_tickets_by_created_date.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--cutoff-date",
            "2026-01-01",
            "--candidate-output-root",
            str(candidate_root),
            "--retrieval-output-root",
            str(retrieval_root),
            "--candidate-manifest-out",
            str(candidate_manifest),
            "--retrieval-manifest-out",
            str(retrieval_manifest),
        ],
    )

    split_tickets_by_created_date_mod.main()

    assert (candidate_root / "INC010" / "99" / "candidate.json").exists()
    assert (candidate_root / "INC010" / "99" / "example.log").exists()
    assert (
        candidate_root
        / "INC010"
        / "99"
        / "candidate_20260212_012659_attachements"
        / "extra.txt"
    ).exists()
    assert (retrieval_root / "INC010" / "99" / "retrieval.json").exists()
    assert not (retrieval_root / "INC010" / "99" / "candidate.json").exists()

    candidate_obj = json.loads(candidate_manifest.read_text(encoding="utf-8"))
    retrieval_obj = json.loads(retrieval_manifest.read_text(encoding="utf-8"))
    assert candidate_obj["source_path"] == str(candidate_root.resolve())
    assert retrieval_obj["source_path"] == str(retrieval_root.resolve())
    assert candidate_obj["counts"]["selected_files"] == 1
    assert retrieval_obj["counts"]["selected_files"] == 1
    assert candidate_obj["counts"]["attachments_copied"] == 2
    assert retrieval_obj["counts"]["attachments_copied"] == 0
    assert candidate_obj["selected_files"] == ["INC010/99/candidate.json"]
    assert retrieval_obj["selected_files"] == ["INC010/99/retrieval.json"]


def test_split_rejects_non_materialized_parent_manifest(tmp_path: Path, monkeypatch):
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
            "split_tickets_by_created_date.py",
            "--selected-corpus-manifest",
            str(selected_manifest),
            "--cutoff-date",
            "2026-01-01",
            "--candidate-output-root",
            str(tmp_path / "candidate_root"),
            "--retrieval-output-root",
            str(tmp_path / "retrieval_root"),
            "--dry-run",
        ],
    )

    with pytest.raises(ValueError, match="non-materialized output"):
        split_tickets_by_created_date_mod.main()
