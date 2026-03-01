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
    source_root = tmp_path / "tickets"
    source_root.mkdir()
    (source_root / "good.json").write_text(
        json.dumps(_valid_ticket_payload()),
        encoding="utf-8",
    )
    (source_root / "bad.json").write_text("{not valid json", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            str(source_root),
            "--dry-run",
        ],
    )

    with pytest.raises(RuntimeError, match="Encountered 1 file processing errors"):
        build_tickets_chroma_mod.main()


def test_main_dry_run_allows_file_errors_with_flag(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "tickets"
    source_root.mkdir()
    (source_root / "good.json").write_text(
        json.dumps(_valid_ticket_payload()),
        encoding="utf-8",
    )
    (source_root / "bad.json").write_text("{not valid json", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_tickets_chroma.py",
            str(source_root),
            "--dry-run",
            "--allow-file-errors",
            "--manifest-out",
            str(manifest_path),
        ],
    )

    build_tickets_chroma_mod.main()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["errors"] == 1
