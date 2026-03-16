from datetime import date
import json
from pathlib import Path
import re

from athos.utils.ticket_ingest import (
    build_full_incident_document,
    compute_corpus_fingerprint,
    evaluate_ticket_filter_reason,
    sanitize_ticket_record,
    write_manifest,
)


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
            "close_code": "Solved (Permanently)",
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


def test_build_full_incident_document_applies_comment_and_note_caps():
    record = _sample_record()
    record["discussions"]["customer_facing_comments"] = [
        {"timestamp": "t1", "created_by": "u", "text": "c" * 80}
    ]
    record["discussions"]["internal_work_notes"] = [
        {"timestamp": "t2", "created_by": "u", "text": "w" * 80}
    ]
    docs = build_full_incident_document(
        record,
        Path("tickets/INC0144695.json"),
        max_comment_chars=30,
        max_work_note_chars=30,
    )
    assert docs[0].metadata["truncated_comments"] is True
    assert docs[0].metadata["truncated_work_notes"] is True


def test_evaluate_ticket_filter_reason_excluded_contact_type():
    reason = evaluate_ticket_filter_reason(
        _sample_record(),
        exclude_contact_types={"Email"},
    )
    assert reason == "excluded_contact_type"


def test_evaluate_ticket_filter_reason_min_created_date():
    reason = evaluate_ticket_filter_reason(
        _sample_record(),
        min_created_date=date(2020, 1, 1),
    )
    assert reason == "created_before_min_date"


def test_evaluate_ticket_filter_reason_regex_exclusions():
    reason = evaluate_ticket_filter_reason(
        _sample_record(),
        exclude_created_by_pattern=re.compile(r"^gue"),
    )
    assert reason == "excluded_created_by_regex"


def test_evaluate_ticket_filter_reason_short_description_exact():
    record = _sample_record()
    record["incident_fields"]["short_description"] = "Ticket from IRIS: New PI Account Request"
    reason = evaluate_ticket_filter_reason(
        record,
        exclude_short_description_exact={"ticket from iris: new pi account request"},
    )
    assert reason == "excluded_short_description_exact"


def test_evaluate_ticket_filter_reason_short_description_prefix():
    record = _sample_record()
    record["incident_fields"]["short_description"] = "Storage Quota Increase Request: project"
    reason = evaluate_ticket_filter_reason(
        record,
        exclude_short_description_prefixes=("storage quota increase request:",),
    )
    assert reason == "excluded_short_description_prefix"


def test_evaluate_ticket_filter_reason_short_description_regex():
    record = _sample_record()
    record["incident_fields"]["short_description"] = "Renewal of GPU training for staff"
    reason = evaluate_ticket_filter_reason(
        record,
        exclude_short_description_patterns=[re.compile(r"^renewal of .+ training for staff$", re.IGNORECASE)],
    )
    assert reason == "excluded_short_description_regex"


def test_evaluate_ticket_filter_reason_no_messages():
    record = _sample_record()
    record["discussions"]["customer_facing_comments"] = []
    record["discussions"]["internal_work_notes"] = []
    reason = evaluate_ticket_filter_reason(
        record,
        exclude_if_no_messages=True,
    )
    assert reason == "excluded_no_messages"


def test_evaluate_ticket_filter_reason_all_messages_from_authors():
    record = _sample_record()
    record["discussions"]["customer_facing_comments"] = [
        {"timestamp": "t1", "created_by": "autoticketing", "text": "msg"}
    ]
    record["discussions"]["internal_work_notes"] = []
    reason = evaluate_ticket_filter_reason(
        record,
        exclude_if_all_messages_from_authors={"autoticketing", "pm-node-info-bot"},
    )
    assert reason == "excluded_all_messages_from_authors"


def test_evaluate_ticket_filter_reason_single_message_no_attachments():
    record = _sample_record()
    record["discussions"]["customer_facing_comments"] = [
        {"timestamp": "t1", "created_by": "user", "text": "msg"}
    ]
    record["discussions"]["internal_work_notes"] = []
    record["attachments"] = []
    reason = evaluate_ticket_filter_reason(
        record,
        exclude_if_single_message_no_attachments=True,
    )
    assert reason == "excluded_single_message_no_attachments"


def test_evaluate_ticket_filter_reason_close_code_not_in_include_list():
    record = _sample_record()
    record["incident_fields"]["close_code"] = "Not Solved (No User Response)"
    reason = evaluate_ticket_filter_reason(
        record,
        include_close_codes={"Solved (Permanently)"},
    )
    assert reason == "close_code_not_in_include_list"


def test_evaluate_ticket_filter_reason_excluded_close_code():
    record = _sample_record()
    reason = evaluate_ticket_filter_reason(
        record,
        exclude_close_codes={"Solved (Permanently)"},
    )
    assert reason == "excluded_close_code"


def test_compute_corpus_fingerprint_is_stable(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "sub" / "b.json"
    b.parent.mkdir()
    a.write_text("{}", encoding="utf-8")
    b.write_text("{}", encoding="utf-8")

    fp1 = compute_corpus_fingerprint(tmp_path, [b, a])
    fp2 = compute_corpus_fingerprint(tmp_path, [a, b])
    assert fp1.file_count == 2
    assert fp1.sha256 == fp2.sha256


def test_compute_corpus_fingerprint_changes_for_selected_subset(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    a.write_text("{}", encoding="utf-8")
    b.write_text("{}", encoding="utf-8")
    c.write_text("{}", encoding="utf-8")

    full = compute_corpus_fingerprint(tmp_path, [a, b, c])
    kept = compute_corpus_fingerprint(tmp_path, [a, c])
    assert full.file_count == 3
    assert kept.file_count == 2
    assert full.sha256 != kept.sha256


def test_write_manifest_creates_parent_dirs(tmp_path):
    manifest_path = tmp_path / "nested" / "run.json"
    payload = {"counts": {"input_files": 1}}
    write_manifest(manifest_path, payload)
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert loaded == payload


def test_sanitize_ticket_record_replaces_structured_users_and_emails():
    record = _sample_record()
    record["incident_fields"]["description"] = "Reach me at jdoe@example.com for updates."
    record["incident_fields"]["assigned_to"] = "consultant@example.com"
    record["incident_fields"]["email"] = "guest@example.com"
    record["discussions"]["customer_facing_comments"][0]["created_by"] = "guest_user"
    record["discussions"]["customer_facing_comments"][0]["text"] = "My email is guest@example.com"

    sanitized, stats = sanitize_ticket_record(record, salt="unit-test-salt")

    assert sanitized["incident_fields"]["assigned_to"].startswith("USER_")
    assert sanitized["incident_fields"]["email"].startswith("EMAIL_")
    assert sanitized["discussions"]["customer_facing_comments"][0]["created_by"].startswith("USER_")
    assert "guest@example.com" not in sanitized["incident_fields"]["description"]
    assert "guest@example.com" not in sanitized["discussions"]["customer_facing_comments"][0]["text"]
    assert "EMAIL_" in sanitized["incident_fields"]["description"]
    assert "EMAIL_" in sanitized["discussions"]["customer_facing_comments"][0]["text"]
    assert stats.structured_user_replacements >= 2
    assert stats.structured_email_replacements == 1
    assert stats.free_text_email_replacements >= 2


def test_sanitize_ticket_record_is_deterministic_for_same_identity():
    record = _sample_record()
    record["incident_fields"]["sys_created_by"] = "Guest"
    record["discussions"]["customer_facing_comments"] = [
        {"timestamp": "t1", "created_by": "guest", "text": "guest@example.com"},
        {"timestamp": "t2", "created_by": "Guest", "text": "guest@example.com"},
    ]

    sanitized, _ = sanitize_ticket_record(record, salt="unit-test-salt")

    first_author = sanitized["discussions"]["customer_facing_comments"][0]["created_by"]
    second_author = sanitized["discussions"]["customer_facing_comments"][1]["created_by"]
    assert first_author == second_author
    assert sanitized["incident_fields"]["sys_created_by"] == first_author


def test_sanitize_ticket_record_scrubs_high_confidence_username_patterns():
    record = _sample_record()
    record["incident_fields"]["caller_id"] = "Doe, Jane (jdoe)"
    record["incident_fields"]["closed_by"] = "Admin, Ops (opsadmin)"
    record["incident_fields"]["u_owner"] = "Admin, Ops (opsadmin)"
    record["discussions"]["customer_facing_comments"][0]["text"] = (
        "Prompt jdoe@cori09:~> ls; path /global/homes/j/jdoe/project; "
        "run squeue -u jdoe; caller_id:jdoe"
    )

    sanitized, stats = sanitize_ticket_record(record, salt="unit-test-salt")

    assert sanitized["incident_fields"]["caller_id"].startswith("USER_")
    assert sanitized["incident_fields"]["closed_by"].startswith("USER_")
    assert sanitized["incident_fields"]["u_owner"].startswith("USER_")
    text = sanitized["discussions"]["customer_facing_comments"][0]["text"]
    assert "jdoe@cori09" not in text
    assert "/global/homes/j/jdoe" not in text
    assert "-u jdoe" not in text
    assert "caller_id:jdoe" not in text
    assert "USER_" in text
    assert stats.free_text_username_replacements >= 4


def test_sanitize_ticket_record_canonicalizes_composite_identity_fields():
    record = _sample_record()
    record["incident_fields"]["watch_list"] = "Bailey, Stephen (sbailey)"
    record["incident_fields"]["u_username_watchlist"] = "Bailey, Stephen (sbailey)"
    record["incident_fields"]["u_itil_watch_list"] = "Bagwell, Clayton (cbagwell), Gerhardt, Lisa (lgerhard)"

    sanitized, stats = sanitize_ticket_record(record, salt="unit-test-salt")

    expected_alias = sanitize_ticket_record(
        {"incident_fields": {"sys_created_by": "sbailey"}},
        salt="unit-test-salt",
    )[0]["incident_fields"]["sys_created_by"]
    assert sanitized["incident_fields"]["watch_list"] == expected_alias
    assert sanitized["incident_fields"]["u_username_watchlist"] == expected_alias
    assert "Bailey" not in sanitized["incident_fields"]["watch_list"]
    itil = sanitized["incident_fields"]["u_itil_watch_list"]
    assert "Clayton" not in itil
    assert "Lisa" not in itil
    assert "USER_" in itil
    assert stats.structured_user_replacements >= 4
