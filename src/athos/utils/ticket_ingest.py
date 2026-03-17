"""Utilities for parsing and normalizing ServiceNow ticket JSON for retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hmac
import hashlib
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


@dataclass(frozen=True)
class CorpusFingerprint:
    """Reproducibility fingerprint for a selected corpus slice."""

    file_count: int
    sha256: str


@dataclass(frozen=True)
class SanitizationStats:
    """Counts emitted while sanitizing one ticket payload."""

    structured_user_replacements: int = 0
    structured_email_replacements: int = 0
    free_text_email_replacements: int = 0
    free_text_username_replacements: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "structured_user_replacements": self.structured_user_replacements,
            "structured_email_replacements": self.structured_email_replacements,
            "free_text_email_replacements": self.free_text_email_replacements,
            "free_text_username_replacements": self.free_text_username_replacements,
        }


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


def _normalize_close_code(value: str) -> str:
    """Normalize close code strings while preserving canonical values."""
    normalized = value.strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {'"', "'"}:
        normalized = normalized[1:-1].strip()
    return normalized


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


def _normalize_state(value: str) -> str:
    return " ".join(value.strip().lower().split())


def evaluate_ticket_filter_reason(
    record: Mapping[str, Any],
    *,
    min_created_date: date | None = None,
    include_contact_types: set[str] | None = None,
    exclude_contact_types: set[str] | None = None,
    include_close_codes: set[str] | None = None,
    exclude_close_codes: set[str] | None = None,
    require_closed_or_resolved_state: bool = False,
    exclude_created_by_pattern: re.Pattern[str] | None = None,
    exclude_assignment_group_pattern: re.Pattern[str] | None = None,
    exclude_short_description_exact: set[str] | None = None,
    exclude_short_description_prefixes: tuple[str, ...] | list[str] | None = None,
    exclude_short_description_patterns: list[re.Pattern[str]] | None = None,
    exclude_if_no_messages: bool = False,
    exclude_if_all_messages_from_authors: set[str] | None = None,
    exclude_if_single_message_no_attachments: bool = False,
) -> str | None:
    """Return a filter reason code if ticket should be skipped, else ``None``."""
    fields = extract_ticket_filter_fields(record)
    metadata = _as_mapping(record.get("metadata"))
    incident_fields = _as_mapping(record.get("incident_fields"))

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

    close_code = _normalize_close_code(_extract_scalar(record, metadata, incident_fields, "close_code"))
    if include_close_codes and close_code not in include_close_codes:
        return "close_code_not_in_include_list"

    if exclude_close_codes and close_code in exclude_close_codes:
        return "excluded_close_code"

    if require_closed_or_resolved_state:
        state = _normalize_state(_extract_scalar(record, metadata, incident_fields, "state", "incident_state"))
        if state not in {"closed", "resolved"}:
            return "state_not_closed_or_resolved"

    if exclude_created_by_pattern and exclude_created_by_pattern.search(fields.created_by):
        return "excluded_created_by_regex"

    if exclude_assignment_group_pattern and exclude_assignment_group_pattern.search(fields.assignment_group):
        return "excluded_assignment_group_regex"

    short_description = _extract_scalar(record, metadata, incident_fields, "short_description")
    short_description_lc = short_description.lower()

    if exclude_short_description_exact and short_description:
        if short_description_lc in {item.lower() for item in exclude_short_description_exact}:
            return "excluded_short_description_exact"

    if exclude_short_description_prefixes and short_description:
        for prefix in exclude_short_description_prefixes:
            if short_description_lc.startswith(prefix.lower()):
                return "excluded_short_description_prefix"

    if exclude_short_description_patterns and short_description:
        for pattern in exclude_short_description_patterns:
            if pattern.search(short_description):
                return "excluded_short_description_regex"

    discussions = _as_mapping(record.get("discussions"))
    message_count = 0
    message_authors: list[str] = []
    for key in ("customer_facing_comments", "internal_work_notes"):
        for entry in _as_list(discussions.get(key)):
            if not isinstance(entry, Mapping):
                continue
            author = _stringify(entry.get("created_by"))
            if author.lower() == "system":
                continue
            text = _stringify(entry.get("text") or entry.get("value") or entry.get("display_value"))
            if not text:
                continue
            message_count += 1
            message_authors.append(author.lower())

    if exclude_if_no_messages and message_count == 0:
        return "excluded_no_messages"

    if exclude_if_all_messages_from_authors and message_count > 0:
        lowered_excluded_authors = {author.lower() for author in exclude_if_all_messages_from_authors}
        if all(author in lowered_excluded_authors for author in message_authors):
            return "excluded_all_messages_from_authors"

    if exclude_if_single_message_no_attachments and message_count == 1:
        attachments = _as_list(record.get("attachments"))
        if not attachments:
            return "excluded_single_message_no_attachments"

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


def compute_corpus_fingerprint(source_root: Path, ticket_files: list[Path]) -> CorpusFingerprint:
    """Compute a stable fingerprint over selected files."""
    digest = hashlib.sha256()
    for path in sorted(ticket_files):
        rel = str(path.relative_to(source_root))
        stat = path.stat()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\n")
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(b"\n")
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))
        digest.update(b"\n")
    return CorpusFingerprint(file_count=len(ticket_files), sha256=digest.hexdigest())


def write_manifest(manifest_out: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON manifest to disk, creating parent directories."""
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with manifest_out.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
USER_FIELD_NAMES = {
    "assigned_to",
    "author",
    "caller_id",
    "closed_by",
    "created_by",
    "opened_by",
    "owner",
    "resolved_by",
    "reopened_by",
    "requested_for",
    "resolved_by",
    "sys_created_by",
    "sys_updated_by",
    "u_owner",
    "u_user",
    "user",
}
COMPOSITE_USER_FIELD_NAMES = {
    "u_itil_watch_list",
    "u_user_watchlist",
    "u_username_watchlist",
    "watch_list",
}
EMAIL_FIELD_NAMES = {
    "email",
    "email_address",
    "u_email_watchlist",
    "u_email",
}
PATH_PRESERVING_FIELD_NAMES = {
    "local_path",
}
USERNAME_CHARS = r"[A-Za-z0-9._-]+"
USERNAME_ALIAS_CHARS = r"[a-z][a-z0-9._-]*"
SHELL_LOGIN_PATTERN = re.compile(rf"\b({USERNAME_CHARS})@([A-Za-z][A-Za-z0-9._-]*)")
HOME_PATH_PATTERN = re.compile(
    rf"(?P<prefix>/(?:global/homes|pscratch/sd|pscratch/sd/[A-Za-z]|global/cfs/cdirs)/[A-Za-z]?/?)(?P<username>{USERNAME_CHARS})"
)
COMMAND_USER_FLAG_PATTERN = re.compile(
    rf"(?P<prefix>(?:^|[\s=])(?:-u|--user)\s+)(?P<username>{USERNAME_CHARS})(?=$|[\s,;:/])"
)
PARSE_FIELD_USERNAME_PATTERN = re.compile(
    rf"(?P<prefix>\b(?:caller_id|opened_by|u_owner|username|user):)(?P<username>{USERNAME_CHARS})\b"
)
PAREN_USERNAME_PATTERN = re.compile(rf"\((?P<username>{USERNAME_ALIAS_CHARS})\)")
USERNAME_IN_PARENS_PATTERN = re.compile(rf"\((?P<username>{USERNAME_ALIAS_CHARS})\)")
HEX_SYS_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)
COMPOSITE_IDENTITY_ENTRY_PATTERN = re.compile(
    rf"""
    \s*
    (?:
        (?P<email>{EMAIL_PATTERN.pattern})
        |
        (?P<name_username>[^,;]+(?:,\s*[^,;]+)?\s+\((?P<wrapped_username>{USERNAME_CHARS})\)(?:\s+[A-Za-z/]+)?)
        |
        (?P<bare_username>{USERNAME_CHARS})
        |
        (?P<sys_id>[0-9a-f]{{32}})
    )
    \s*
    (?:,|;|$)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _build_deterministic_alias(kind: str, raw_value: str, salt: str) -> str:
    normalized = raw_value.strip().lower()
    digest = hmac.new(
        salt.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:10].upper()
    return f"{kind}_{digest}"


def _sanitize_free_text_emails(
    text: str,
    *,
    salt: str,
) -> tuple[str, int]:
    replacements = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal replacements
        replacements += 1
        return _build_deterministic_alias("EMAIL", match.group(0), salt)

    return EMAIL_PATTERN.sub(_replace, text), replacements


def _sanitize_free_text_usernames(
    text: str,
    *,
    salt: str,
) -> tuple[str, int]:
    replacements = 0

    def _user_alias(raw_value: str) -> str:
        nonlocal replacements
        replacements += 1
        return _build_deterministic_alias("USER", raw_value, salt)

    def _replace_shell_login(match: re.Match[str]) -> str:
        return f"{_user_alias(match.group(1))}@{match.group(2)}"

    def _replace_home_path(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{_user_alias(match.group('username'))}"

    def _replace_flag(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{_user_alias(match.group('username'))}"

    def _replace_parse_field(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{_user_alias(match.group('username'))}"

    def _replace_paren_username(match: re.Match[str]) -> str:
        return f"({_user_alias(match.group('username'))})"

    sanitized = SHELL_LOGIN_PATTERN.sub(_replace_shell_login, text)
    sanitized = HOME_PATH_PATTERN.sub(_replace_home_path, sanitized)
    sanitized = COMMAND_USER_FLAG_PATTERN.sub(_replace_flag, sanitized)
    sanitized = PARSE_FIELD_USERNAME_PATTERN.sub(_replace_parse_field, sanitized)
    sanitized = PAREN_USERNAME_PATTERN.sub(_replace_paren_username, sanitized)
    return sanitized, replacements


def _canonicalize_identity_token(value: str) -> tuple[str, str]:
    stripped = value.strip()
    email_match = EMAIL_PATTERN.fullmatch(stripped)
    if email_match:
        return "EMAIL", stripped
    username_match = USERNAME_IN_PARENS_PATTERN.search(stripped)
    if username_match:
        return "USER", username_match.group("username")
    if HEX_SYS_ID_PATTERN.fullmatch(stripped):
        return "USER", stripped
    return "USER", stripped


def _sanitize_composite_identity_list(
    text: str,
    *,
    salt: str,
) -> tuple[str, int, int]:
    sanitized_entries: list[str] = []
    user_replacements = 0
    email_replacements = 0
    position = 0
    while position < len(text):
        match = COMPOSITE_IDENTITY_ENTRY_PATTERN.match(text, position)
        if not match:
            remainder = text[position:].strip()
            if remainder:
                kind, canonical = _canonicalize_identity_token(remainder)
                if kind == "EMAIL":
                    sanitized_entries.append(_build_deterministic_alias("EMAIL", canonical, salt))
                    email_replacements += 1
                else:
                    sanitized_entries.append(_build_deterministic_alias("USER", canonical, salt))
                    user_replacements += 1
            break

        if match.group("email"):
            kind, canonical = "EMAIL", match.group("email")
        elif match.group("wrapped_username"):
            kind, canonical = "USER", match.group("wrapped_username")
        elif match.group("sys_id"):
            kind, canonical = "USER", match.group("sys_id")
        else:
            kind, canonical = "USER", match.group("bare_username")

        if kind == "EMAIL":
            sanitized_entries.append(_build_deterministic_alias("EMAIL", canonical, salt))
            email_replacements += 1
        else:
            sanitized_entries.append(_build_deterministic_alias("USER", canonical, salt))
            user_replacements += 1
        position = match.end()

    if not sanitized_entries:
        return text, 0, 0
    return ", ".join(sanitized_entries), user_replacements, email_replacements


def sanitize_ticket_record(
    record: Mapping[str, Any],
    *,
    salt: str,
) -> tuple[dict[str, Any], SanitizationStats]:
    """Return a deep-copied ticket record with basic identity fields sanitized."""
    payload = json.loads(json.dumps(record))
    stats = SanitizationStats()

    def _sanitize(value: Any, key_hint: str | None = None) -> Any:
        nonlocal stats
        if isinstance(value, dict):
            return {key: _sanitize(item, key) for key, item in value.items()}
        if isinstance(value, list):
            return [_sanitize(item, key_hint) for item in value]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return value
            key_name = (key_hint or "").lower()
            if key_name in PATH_PRESERVING_FIELD_NAMES:
                return value
            if key_name in EMAIL_FIELD_NAMES:
                stats = SanitizationStats(
                    structured_user_replacements=stats.structured_user_replacements,
                    structured_email_replacements=stats.structured_email_replacements + 1,
                    free_text_email_replacements=stats.free_text_email_replacements,
                    free_text_username_replacements=stats.free_text_username_replacements,
                )
                return _build_deterministic_alias("EMAIL", stripped, salt)
            if key_name in COMPOSITE_USER_FIELD_NAMES:
                sanitized_list, user_replacements, email_replacements = _sanitize_composite_identity_list(
                    stripped,
                    salt=salt,
                )
                stats = SanitizationStats(
                    structured_user_replacements=stats.structured_user_replacements + user_replacements,
                    structured_email_replacements=stats.structured_email_replacements + email_replacements,
                    free_text_email_replacements=stats.free_text_email_replacements,
                    free_text_username_replacements=stats.free_text_username_replacements,
                )
                return sanitized_list
            if key_name in USER_FIELD_NAMES:
                stats = SanitizationStats(
                    structured_user_replacements=stats.structured_user_replacements + 1,
                    structured_email_replacements=stats.structured_email_replacements,
                    free_text_email_replacements=stats.free_text_email_replacements,
                    free_text_username_replacements=stats.free_text_username_replacements,
                )
                return _build_deterministic_alias("USER", stripped, salt)
            sanitized, replacements = _sanitize_free_text_emails(stripped, salt=salt)
            username_sanitized, username_replacements = _sanitize_free_text_usernames(
                sanitized,
                salt=salt,
            )
            if replacements or username_replacements:
                stats = SanitizationStats(
                    structured_user_replacements=stats.structured_user_replacements,
                    structured_email_replacements=stats.structured_email_replacements,
                    free_text_email_replacements=stats.free_text_email_replacements + replacements,
                    free_text_username_replacements=(
                        stats.free_text_username_replacements + username_replacements
                    ),
                )
                return username_sanitized
        return value

    return _sanitize(payload), stats


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
