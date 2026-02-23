from pathlib import Path

from athos.utils.ticket_ingest import build_full_incident_document


def _sample_record():
    return {
        "metadata": {
            "incident_number": "INC0144695",
            "sys_id": "abc123",
        },
        "incident_fields": {
            "state": "Closed",
            "category": "Software",
            "subcategory": "",
            "assignment_group": "Consulting",
            "sys_created_on": "2019-09-20 13:08:22",
            "sys_updated_on": "2022-11-09 02:00:04",
            "short_description": "fail for module load slatec",
            "description": "module load error",
            "contact_type": "Email",
            "sys_created_by": "guest",
            "assigned_to": "consultant",
            "priority": "3 - Moderate",
        },
        "discussions": {
            "customer_facing_comments": [
                {
                    "timestamp": "2019-09-20 13:54:23",
                    "created_by": "Guest",
                    "text": "it looks like both pgplot and slatec...",
                }
            ],
            "internal_work_notes": [
                {
                    "timestamp": "2019-09-20 13:10:00",
                    "created_by": "consultant",
                    "text": "tracking module rebuild",
                }
            ],
        },
        "attachments": [
            {
                "file_name": {"value": "example.log", "display_value": "example.log"},
                "content_type": {"value": "text/plain"},
                "size_bytes": {"value": "12345"},
            }
        ],
    }


def test_build_full_incident_document_includes_sections_and_metadata():
    docs = build_full_incident_document(_sample_record(), Path("tickets/INC0144695.json"))
    assert len(docs) == 1
    doc = docs[0]
    assert doc.doc_id == "INC0144695:full"
    assert "CUSTOMER_COMMENTS:" in doc.text
    assert "INTERNAL_WORK_NOTES:" in doc.text
    assert "- example.log (text/plain, 12345 bytes)" in doc.text
    assert doc.metadata["doc_kind"] == "full_incident"
    assert doc.metadata["source_json_path"] == "tickets/INC0144695.json"
    assert doc.metadata["has_attachments"] is True
    assert doc.metadata["chunk_index"] == 0
    assert doc.metadata["chunk_count"] == 1


def test_build_full_incident_document_uses_sys_id_fallback_for_id():
    record = _sample_record()
    del record["metadata"]["incident_number"]
    docs = build_full_incident_document(record, Path("tickets/abc123.json"))
    assert docs[0].doc_id == "abc123:full"


def test_build_full_incident_document_splits_when_max_chars_exceeded():
    record = _sample_record()
    record["incident_fields"]["description"] = "x" * 180
    docs = build_full_incident_document(record, Path("tickets/INC0144695.json"), max_chars=80)
    assert len(docs) > 1
    assert docs[0].doc_id.startswith("INC0144695:full:chunk_")
    assert docs[0].metadata["chunk_count"] == len(docs)
