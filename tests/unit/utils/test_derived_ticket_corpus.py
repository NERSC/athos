import json
from pathlib import Path

from athos.utils.derived_ticket_corpus import (
    DerivedFieldLimits,
    build_attachment_context,
    coerce_derived_payload,
    build_derived_ticket_document,
    contains_email_like_pii,
    derived_ticket_materialized_relpath,
    extract_json_object,
    find_derived_payload_violations,
    normalize_derived_payload,
    render_derived_retrieval_document,
    render_derived_ticket_markdown,
    render_ticket_transform_input,
)


def _record() -> dict:
    return {
        "metadata": {
            "incident_number": "INC0001",
            "sys_id": "sys_inc_1",
        },
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
                {"timestamp": "2025-01-01 00:00:00", "created_by": "USER_A", "text": "first"},
                {"timestamp": "2025-01-01 01:00:00", "created_by": "USER_A", "text": "latest fix context"},
            ],
            "internal_work_notes": [
                {"timestamp": "2025-01-01 02:00:00", "created_by": "USER_B", "text": "rebuilt env"},
            ],
        },
        "attachments": [
            {
                "file_name": {"value": "env.log"},
                "local_path": "servicenow_incidents/INC001/01/env.log",
                "content_type": {"value": "text/plain"},
                "size_bytes": {"value": "120"},
            }
        ],
    }


def test_build_attachment_context_selects_high_signal_lines(tmp_path: Path):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    attachment_path = incident_dir / "env.log"
    attachment_path.write_text(
        "\n".join(
            [
                "header noise",
                "ModuleNotFoundError: No module named 'numpy'",
                "$ module load cray-python",
                "footer noise",
            ]
        ),
        encoding="utf-8",
    )

    context = build_attachment_context(
        _record(),
        source_json_path=incident_dir / "ticket.json",
        source_root=source_root,
        max_total_context_chars=500,
    )

    rendered = "\n".join(context.rendered_lines)
    assert context.attachments_considered == 1
    assert context.attachments_rendered == 1
    assert "ModuleNotFoundError" in rendered
    assert "module load" in rendered


def test_render_ticket_transform_input_prefers_latest_messages(tmp_path: Path):
    source_root = tmp_path / "servicenow_incidents"
    incident_dir = source_root / "INC001" / "01"
    incident_dir.mkdir(parents=True)
    (incident_dir / "env.log").write_text("short attachment", encoding="utf-8")

    rendered = render_ticket_transform_input(
        _record(),
        source_json_path=incident_dir / "ticket.json",
        source_root=source_root,
        max_comment_chars=30,
    )

    assert "latest fix context" in rendered.text
    assert "first" not in rendered.text
    assert "ATTACHMENT_TEXT_SNIPPETS:" in rendered.text


def test_normalize_and_validate_payload():
    payload = normalize_derived_payload(
        {
            "incident_summary": " numpy import failed because the environment was missing a module path. ",
            "resolution_summary": " rebuilt env ",
            "retrieval_keywords": [" numpy ", "import error", ""],
            "evidence_snippets": ["ModuleNotFoundError"],
        }
    )
    violations = find_derived_payload_violations(
        payload,
        limits=DerivedFieldLimits(),
    )

    assert payload["incident_summary"].startswith("numpy import failed")
    assert payload["retrieval_keywords"] == ["numpy", "import error"]
    assert violations == []


def test_coerce_payload_only_trims_lists():
    payload = coerce_derived_payload(
        {
            "incident_summary": "contact user@example.com about the import failure",
            "resolution_summary": "call 510-555-1212 after environment rebuild",
            "retrieval_keywords": ["numpy"] * 20,
            "evidence_snippets": [
                "ModuleNotFoundError",
                "user@example.com",
                "510-555-1212",
                "second useful snippet",
            ],
        },
        limits=DerivedFieldLimits(max_keywords=3, max_evidence_snippets=2),
    )

    assert payload["incident_summary"] == "contact user@example.com about the import failure"
    assert payload["resolution_summary"] == "call 510-555-1212 after environment rebuild"
    assert payload["retrieval_keywords"] == ["numpy", "numpy", "numpy"]
    assert payload["evidence_snippets"] == ["ModuleNotFoundError", "user@example.com"]


def test_validate_payload_rejects_pii_and_limit_overruns():
    payload = {
        "incident_summary": "x" * 1201,
        "resolution_summary": "contact me at user@example.com",
        "retrieval_keywords": ["numpy"] * 13,
        "evidence_snippets": [],
    }

    violations = find_derived_payload_violations(
        payload,
        limits=DerivedFieldLimits(),
    )

    assert "incident_summary exceeds 1200 chars" in violations
    assert "resolution_summary contains email address" in violations
    assert "retrieval_keywords exceeds 12 items" in violations


def test_email_detector_ignores_linker_symbol_false_positive():
    assert not contains_email_like_pii(
        "__cudaRegisterFatBinary@libcudart.so.11.0"
    )
    assert contains_email_like_pii("contact user@example.com for access")


def test_extract_json_object_supports_fenced_output():
    raw = """```json
{"incident_summary":"a","resolution_summary":"b","retrieval_keywords":["x"],"evidence_snippets":[]}
```"""

    extracted = extract_json_object(raw)
    assert json.loads(extracted)["incident_summary"] == "a"


def test_render_derived_retrieval_document():
    rendered = render_derived_retrieval_document(
        {
            "incident_summary": "numpy import failed in a python environment after a broken module load.",
            "resolution_summary": "rebuilt env",
            "retrieval_keywords": ["numpy", "import error"],
            "evidence_snippets": ["ModuleNotFoundError"],
        }
    )

    assert "INCIDENT_SUMMARY:" in rendered
    assert "- numpy" in rendered
    assert "- ModuleNotFoundError" in rendered


def test_build_derived_ticket_document_and_markdown():
    payload = {
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
        "evidence_snippets": ["fatal error: gsl/gsl_sf.h: No such file or directory"],
        "schema_version": "athos.derived_ticket_record.v2",
        "source_json_path": "/tmp/INC0196020.json",
    }

    doc = build_derived_ticket_document(payload)
    assert doc.doc_id == "INC0196020::derived"
    assert doc.metadata["record_type"] == "derived_ticket"
    assert "INCIDENT_SUMMARY:" in doc.text

    markdown = render_derived_ticket_markdown(payload)
    assert "# INC0196020" in markdown
    assert "## Incident Summary" in markdown
    assert "module load error" in markdown

    rel_path = derived_ticket_materialized_relpath(payload)
    assert rel_path == Path("INC019") / "60" / "20.md"
