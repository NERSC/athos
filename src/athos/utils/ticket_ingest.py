"""Utilities for parsing and normalizing ServiceNow ticket JSON for retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TicketDocument:
    """Normalized document payload ready for indexing."""

    doc_id: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class TicketFilterFields:
    """Fields used for ingestion filtering decisions."""

    incident_number: str
    sys_created_on: str
    contact_type: str
    created_by: str
    assignment_group: str


@dataclass(frozen=True)
class SectionCapResult:
    """Result of applying a max-character cap to a discussion section."""

    lines: list[str]
    truncated: bool


def iter_ticket_json_files(source_root: Path) -> Iterable[Path]:
    """Yield ticket JSON files in deterministic order."""
    return sorted(source_root.rglob("*.json"))


def load_ticket_json(path: Path) -> dict[str, Any]:
    """Load and validate one ticket JSON object."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}, got {type(payload).__name__}")
    return payload


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Mapping):
        stable = value.get("value")
        if isinstance(stable, str) and stable.strip():
            return stable.strip()
        display = value.get("display_value")
        if isinstance(display, str) and display.strip():
            return display.strip()
    return ""


def _extract_scalar(
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    incident_fields: Mapping[str, Any],
    *keys: str,
) -> str:
    for key in keys:
        for source in (metadata, incident_fields, record):
            text = _stringify(source.get(key))
            if text:
                return text
    return ""


def _extract_bool(
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    incident_fields: Mapping[str, Any],
    *keys: str,
) -> bool:
    raw = _extract_scalar(record, metadata, incident_fields, *keys).lower()
    return raw in {"1", "true", "yes"}


def _format_discussion_line(entry: Mapping[str, Any]) -> str:
    timestamp = _stringify(entry.get("timestamp") or entry.get("created_on"))
    author = _stringify(entry.get("created_by") or entry.get("author") or entry.get("user"))
    text = _stringify(entry.get("text") or entry.get("value") or entry.get("display_value"))
    if not text:
        return ""
    prefix = ""
    if timestamp:
        prefix += f"[{timestamp}] "
    if author:
        prefix += f"{author}: "
    return f"{prefix}{text}" if prefix else text


def _format_attachment_line(entry: Mapping[str, Any]) -> str:
    name = _stringify(entry.get("file_name") or entry.get("name"))
    content_type = _stringify(entry.get("content_type") or entry.get("mime_type"))
    size = _stringify(entry.get("size_bytes") or entry.get("size"))
    details: list[str] = []
    if content_type:
        details.append(content_type)
    if size:
        details.append(f"{size} bytes")
    if name and details:
        return f"{name} ({', '.join(details)})"
    if name:
        return name
    if details:
        return ", ".join(details)
    return ""


def extract_ticket_filter_fields(record: Mapping[str, Any]) -> TicketFilterFields:
    """Extract filter-relevant fields from a ticket record."""
    metadata = _as_mapping(record.get("metadata"))
    incident_fields = _as_mapping(record.get("incident_fields"))
    return TicketFilterFields(
        incident_number=_extract_scalar(record, metadata, incident_fields, "incident_number", "number"),
        sys_created_on=_extract_scalar(record, metadata, incident_fields, "sys_created_on", "created_on"),
        contact_type=_extract_scalar(record, metadata, incident_fields, "contact_type"),
        created_by=_extract_scalar(record, metadata, incident_fields, "sys_created_by", "created_by"),
        assignment_group=_extract_scalar(
            record,
            metadata,
            incident_fields,
            "assignment_group",
            "assignment_group_name",
        ),
    )


def _parse_created_date(value: str) -> date | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) >= 10:
        prefix = value[:10]
        try:
            return datetime.strptime(prefix, "%Y-%m-%d").date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def evaluate_ticket_filter_reason(
    record: Mapping[str, Any],
    *,
    min_created_date: date | None = None,
    include_contact_types: set[str] | None = None,
    exclude_contact_types: set[str] | None = None,
    exclude_created_by_pattern: re.Pattern[str] | None = None,
    exclude_assignment_group_pattern: re.Pattern[str] | None = None,
) -> str | None:
    """Return a filter reason code if ticket should be skipped, else ``None``."""
    fields = extract_ticket_filter_fields(record)

    if min_created_date is not None:
        created_date = _parse_created_date(fields.sys_created_on)
        if created_date is None:
            return "missing_or_invalid_created_date"
        if created_date < min_created_date:
            return "created_before_min_date"

    if include_contact_types:
        if fields.contact_type not in include_contact_types:
            return "contact_type_not_in_include_list"

    if exclude_contact_types and fields.contact_type in exclude_contact_types:
        return "excluded_contact_type"

    if exclude_created_by_pattern and exclude_created_by_pattern.search(fields.created_by):
        return "excluded_created_by_regex"

    if exclude_assignment_group_pattern and exclude_assignment_group_pattern.search(fields.assignment_group):
        return "excluded_assignment_group_regex"

    return None


def _cap_lines(lines: list[str], max_chars: int | None) -> SectionCapResult:
    if max_chars is None or max_chars <= 0:
        return SectionCapResult(lines=lines, truncated=False)
    joined = "\n".join(lines)
    if len(joined) <= max_chars:
        return SectionCapResult(lines=lines, truncated=False)
    clipped = joined[:max_chars].rstrip()
    if not clipped:
        return SectionCapResult(lines=[], truncated=True)
    return SectionCapResult(lines=clipped.splitlines(), truncated=True)


def build_full_incident_document(
    record: Mapping[str, Any],
    source_json_path: Path,
    *,
    max_chars: int | None = None,
    max_comment_chars: int | None = None,
    max_work_note_chars: int | None = None,
) -> list[TicketDocument]:
    """Create one full-incident document with deterministic IDs and optional chunk fallback."""
    metadata = _as_mapping(record.get("metadata"))
    incident_fields = _as_mapping(record.get("incident_fields"))
    discussions = _as_mapping(record.get("discussions"))
    attachments = _as_list(record.get("attachments"))

    incident_number = _extract_scalar(record, metadata, incident_fields, "incident_number", "number")
    sys_id = _extract_scalar(record, metadata, incident_fields, "sys_id")
    state = _extract_scalar(record, metadata, incident_fields, "state")
    category = _extract_scalar(record, metadata, incident_fields, "category")
    subcategory = _extract_scalar(record, metadata, incident_fields, "subcategory")
    assignment_group = _extract_scalar(
        record,
        metadata,
        incident_fields,
        "assignment_group",
        "assignment_group_name",
    )
    created_on = _extract_scalar(record, metadata, incident_fields, "sys_created_on", "created_on")
    updated_on = _extract_scalar(record, metadata, incident_fields, "sys_updated_on", "updated_on")
    contact_type = _extract_scalar(record, metadata, incident_fields, "contact_type")
    created_by = _extract_scalar(record, metadata, incident_fields, "sys_created_by", "created_by")
    short_description = _extract_scalar(record, metadata, incident_fields, "short_description")
    description = _extract_scalar(record, metadata, incident_fields, "description")
    assigned_to = _extract_scalar(record, metadata, incident_fields, "assigned_to")
    priority = _extract_scalar(record, metadata, incident_fields, "priority")
    has_attachments = _extract_bool(record, metadata, incident_fields, "has_attachments")

    customer_comments_raw = [
        _format_discussion_line(entry)
        for entry in _as_list(discussions.get("customer_facing_comments"))
        if isinstance(entry, Mapping)
    ]
    customer_comments_raw = [line for line in customer_comments_raw if line]
    customer_comments_result = _cap_lines(customer_comments_raw, max_comment_chars)
    customer_comments = customer_comments_result.lines

    work_notes_raw = [
        _format_discussion_line(entry)
        for entry in _as_list(discussions.get("internal_work_notes"))
        if isinstance(entry, Mapping)
    ]
    work_notes_raw = [line for line in work_notes_raw if line]
    work_notes_result = _cap_lines(work_notes_raw, max_work_note_chars)
    work_notes = work_notes_result.lines

    attachment_lines = [
        _format_attachment_line(entry)
        for entry in attachments
        if isinstance(entry, Mapping)
    ]
    attachment_lines = [line for line in attachment_lines if line]
    has_attachments = has_attachments or bool(attachment_lines)

    lines = [
        f"INCIDENT: {incident_number}",
        f"SYS_ID: {sys_id}",
        f"STATE: {state}",
        f"CATEGORY: {category}",
        f"SUBCATEGORY: {subcategory}",
        f"ASSIGNMENT_GROUP: {assignment_group}",
        f"ASSIGNED_TO: {assigned_to}",
        f"PRIORITY: {priority}",
        f"CREATED: {created_on}",
        f"UPDATED: {updated_on}",
        f"SHORT_DESCRIPTION: {short_description}",
        "DESCRIPTION:",
        description,
        "",
        "CUSTOMER_COMMENTS:",
    ]
    lines.extend(customer_comments or [""])
    lines.extend(["", "INTERNAL_WORK_NOTES:"])
    lines.extend(work_notes or [""])
    lines.extend(["", "ATTACHMENTS_METADATA:"])
    if attachment_lines:
        lines.extend(f"- {line}" for line in attachment_lines)
    else:
        lines.append("")
    full_text = "\n".join(lines).strip()

    base_id = incident_number or sys_id or source_json_path.stem
    full_id = f"{base_id}:full"
    chunks = [full_text]
    if max_chars and max_chars > 0 and len(full_text) > max_chars:
        chunks = [full_text[i : i + max_chars] for i in range(0, len(full_text), max_chars)]

    docs: list[TicketDocument] = []
    chunk_count = len(chunks)
    for chunk_index, chunk in enumerate(chunks):
        doc_id = full_id if chunk_count == 1 else f"{full_id}:chunk_{chunk_index}"
        doc_meta = {
            "incident_number": incident_number,
            "sys_id": sys_id,
            "state": state,
            "category": category,
            "subcategory": subcategory,
            "assignment_group": assignment_group,
            "sys_created_on": created_on,
            "sys_updated_on": updated_on,
            "contact_type": contact_type,
            "created_by": created_by,
            "has_attachments": has_attachments,
            "doc_kind": "full_incident",
            "source_json_path": str(source_json_path),
            "chunk_index": chunk_index,
            "chunk_count": chunk_count,
            "truncated_comments": customer_comments_result.truncated,
            "truncated_work_notes": work_notes_result.truncated,
        }
        docs.append(TicketDocument(doc_id=doc_id, text=chunk, metadata=doc_meta))
    return docs
