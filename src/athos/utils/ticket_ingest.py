"""Utilities for parsing and normalizing ServiceNow ticket JSON for retrieval."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TicketDocument:
    """Normalized document payload ready for indexing."""

    doc_id: str
    text: str
    metadata: dict[str, Any]


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


def build_full_incident_document(
    record: Mapping[str, Any],
    source_json_path: Path,
    *,
    max_chars: int | None = None,
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

    customer_comments = [
        _format_discussion_line(entry)
        for entry in _as_list(discussions.get("customer_facing_comments"))
        if isinstance(entry, Mapping)
    ]
    customer_comments = [line for line in customer_comments if line]

    work_notes = [
        _format_discussion_line(entry)
        for entry in _as_list(discussions.get("internal_work_notes"))
        if isinstance(entry, Mapping)
    ]
    work_notes = [line for line in work_notes if line]

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
        }
        docs.append(TicketDocument(doc_id=doc_id, text=chunk, metadata=doc_meta))
    return docs
