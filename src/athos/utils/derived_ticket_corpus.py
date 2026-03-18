"""Deterministic helpers for building a derived ServiceNow ticket corpus."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable, Mapping

from athos.utils.ticket_ingest import TicketDocument


DEFAULT_ATTACHMENT_TEXT_EXTENSIONS = {
    "txt",
    "log",
    "out",
    "err",
    "csv",
    "tsv",
    "json",
    "yaml",
    "yml",
    "xml",
    "md",
    "sh",
    "py",
}

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"""
    (?<!\w)
    (?:
        \+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}
        |
        \(\d{3}\)\s*\d{3}[-.\s]?\d{4}
        |
        \d{3}[-.]\d{3}[-.]\d{4}
        |
        \d{3}\s\d{3}\s\d{4}
    )
    (?!\w)
    """,
    re.VERBOSE,
)
JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
HIGH_SIGNAL_ATTACHMENT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\berror\b",
        r"\bexception\b",
        r"\btraceback\b",
        r"\bfailed\b",
        r"\binvalid\b",
        r"\bdenied\b",
        r"\bnot found\b",
        r"\btimeout\b",
        r"\boom\b",
        r"\bmodule load\b",
        r"\bpython\b",
        r"\bpip\b",
        r"\bconda\b",
        r"\bsrun\b",
        r"\bsbatch\b",
        r"\bquota\b",
        r"\bfilesystem\b",
        r"/global/",
        r"/pscratch/",
        r"\bjob\s*\d+\b",
        r"\b[A-Z_][A-Z0-9_]*=",
    )
]

LIB_SYMBOL_EMAIL_FALSE_POSITIVE_PATTERN = re.compile(
    r"@[A-Za-z0-9_.+-]+\.so(?:\.\d+)*\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AttachmentSnippet:
    """One selected snippet or full-text excerpt from an attachment."""

    attachment_name: str
    selection_mode: str
    text: str


@dataclass(frozen=True)
class AttachmentContext:
    """Rendered attachment context plus audit metadata."""

    rendered_lines: list[str]
    attachments_considered: int
    attachments_rendered: int
    attachment_summaries: list[dict[str, Any]]


@dataclass(frozen=True)
class RenderedTicketInput:
    """Deterministically rendered transform input plus audit metadata."""

    text: str
    attachment_context: AttachmentContext
    prompt_sha256: str


@dataclass(frozen=True)
class DerivedFieldLimits:
    """Schema and length limits for derived fields."""

    incident_summary_chars: int = 1200
    resolution_summary_chars: int = 800
    max_keywords: int = 12
    max_evidence_snippets: int = 8


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


def _cap_lines_from_end(lines: list[str], max_chars: int | None) -> tuple[list[str], bool]:
    if max_chars is None or max_chars <= 0:
        return lines, False
    selected: list[str] = []
    total_chars = 0
    for line in reversed(lines):
        added = len(line) + (1 if selected else 0)
        if selected and total_chars + added > max_chars:
            break
        if not selected and len(line) > max_chars:
            return [line[-max_chars:]], True
        selected.append(line)
        total_chars += added
    selected.reverse()
    truncated = len(selected) != len(lines)
    return selected, truncated


def _extract_attachment_local_paths(record: Mapping[str, Any]) -> list[str]:
    attachments = record.get("attachments")
    if not isinstance(attachments, list):
        return []
    local_paths: list[str] = []
    for entry in attachments:
        if not isinstance(entry, Mapping):
            continue
        local_path = _stringify(entry.get("local_path"))
        if local_path:
            local_paths.append(local_path)
    return local_paths


def _iter_attachment_dir_candidates(ticket_file: Path) -> Iterable[Path]:
    expected_prefix = f"{ticket_file.stem}_"
    for child in sorted(ticket_file.parent.iterdir()):
        if not child.is_dir():
            continue
        name_lower = child.name.lower()
        if name_lower.endswith("_attachements") or name_lower.endswith("_attachments"):
            if child.name.startswith(expected_prefix):
                yield child


def _resolve_attachment_candidate(local_path: str, *, source_root: Path) -> Path | None:
    source_root_resolved = source_root.resolve()

    def _resolve_if_allowed(candidate: Path) -> Path | None:
        resolved = candidate.resolve()
        if not resolved.exists():
            return None
        try:
            resolved.relative_to(source_root_resolved)
        except ValueError:
            return None
        return resolved

    def _normalized_variants(candidate: Path) -> list[Path]:
        text = str(candidate)
        variants: list[Path] = []
        seen: set[str] = set()
        for form in ("NFC", "NFD"):
            normalized = unicodedata.normalize(form, text)
            if normalized not in seen:
                seen.add(normalized)
                variants.append(Path(normalized))
        return variants

    def _resolve_via_normalized_filename(candidate: Path) -> Path | None:
        parent = candidate.parent
        if not parent.exists() or not parent.is_dir():
            return None
        target_name_nfc = unicodedata.normalize("NFC", candidate.name)
        target_name_nfd = unicodedata.normalize("NFD", candidate.name)
        for child in parent.iterdir():
            child_name_nfc = unicodedata.normalize("NFC", child.name)
            child_name_nfd = unicodedata.normalize("NFD", child.name)
            if child_name_nfc == target_name_nfc or child_name_nfd == target_name_nfd:
                return _resolve_if_allowed(child)
        return None

    candidate = Path(local_path)
    if candidate.is_absolute():
        return None

    raw_candidates = [source_root / candidate]
    parts = list(candidate.parts)
    if parts and parts[0] == source_root.name:
        raw_candidates.append(source_root / Path(*parts[1:]))

    for raw_candidate in raw_candidates:
        joined = _resolve_if_allowed(raw_candidate)
        if joined is not None:
            return joined
        for normalized_candidate in _normalized_variants(raw_candidate):
            resolved = _resolve_if_allowed(normalized_candidate)
            if resolved is not None:
                return resolved
        filename_match = _resolve_via_normalized_filename(raw_candidate)
        if filename_match is not None:
            return filename_match
    return None


def _guess_is_text_attachment(path: Path, *, allowed_extensions: set[str]) -> bool:
    ext = path.suffix.lower().lstrip(".")
    return bool(ext and ext in allowed_extensions)


def _decode_attachment_text(path: Path, *, max_chars: int) -> str | None:
    raw = path.read_bytes()[: max_chars * 4]
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            decoded = raw.decode(encoding)
            normalized = decoded.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
            return normalized[:max_chars]
        except UnicodeDecodeError:
            continue
    return None


def _line_score(line: str) -> int:
    score = 0
    stripped = line.strip()
    if not stripped:
        return score
    for pattern in HIGH_SIGNAL_ATTACHMENT_PATTERNS:
        if pattern.search(stripped):
            score += 5
    if stripped.startswith(("$ ", "# ", "Traceback")):
        score += 3
    if "/" in stripped or "=" in stripped or ":" in stripped:
        score += 1
    return score


def _select_attachment_snippets(
    text: str,
    *,
    max_snippets: int,
    max_snippet_chars: int,
    full_attachment_max_chars: int,
    full_attachment_max_lines: int,
) -> tuple[str, str, int]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", "empty", 0

    if len(text) <= full_attachment_max_chars and len(lines) <= full_attachment_max_lines:
        return text.strip()[:full_attachment_max_chars], "full_text", 1

    scored_lines = [(idx, _line_score(line), line) for idx, line in enumerate(lines)]
    chosen = [(idx, score, line) for idx, score, line in scored_lines if score > 0]
    if not chosen:
        chosen = scored_lines[:max_snippets]
    else:
        chosen.sort(key=lambda item: (-item[1], item[0]))
        chosen = chosen[:max_snippets]
        chosen.sort(key=lambda item: item[0])

    snippet_lines = [line[:max_snippet_chars].rstrip() for _, _, line in chosen if line]
    return "\n".join(snippet_lines), "snippets", len(snippet_lines)


def build_attachment_context(
    record: Mapping[str, Any],
    *,
    source_json_path: Path,
    source_root: Path,
    allowed_extensions: set[str] | None = None,
    max_attachments: int = 3,
    max_attachment_chars: int = 20000,
    max_total_context_chars: int = 2000,
    max_snippets_per_attachment: int = 3,
    max_snippet_chars: int = 300,
    full_attachment_max_chars: int = 2000,
    full_attachment_max_lines: int = 40,
) -> AttachmentContext:
    """Build bounded deterministic attachment text context for one ticket."""
    allowed = allowed_extensions or set(DEFAULT_ATTACHMENT_TEXT_EXTENSIONS)
    attachments = _as_list(record.get("attachments"))
    resolved_files: list[tuple[str, Path]] = []
    seen_paths: set[Path] = set()

    for entry in attachments:
        if not isinstance(entry, Mapping):
            continue
        local_path = _stringify(entry.get("local_path"))
        attachment_name = _stringify(entry.get("file_name") or entry.get("name")) or Path(local_path).name
        if not local_path:
            continue
        resolved = _resolve_attachment_candidate(local_path, source_root=source_root)
        if resolved is None or resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        resolved_files.append((attachment_name or resolved.name, resolved))

    if not resolved_files:
        for attachment_dir in _iter_attachment_dir_candidates(source_json_path):
            for file_path in sorted(attachment_dir.rglob("*")):
                if not file_path.is_file() or file_path in seen_paths:
                    continue
                seen_paths.add(file_path)
                resolved_files.append((file_path.name, file_path))

    rendered_lines: list[str] = []
    attachment_summaries: list[dict[str, Any]] = []
    total_chars = 0
    rendered_count = 0

    for attachment_name, attachment_path in resolved_files:
        if rendered_count >= max_attachments or total_chars >= max_total_context_chars:
            break
        if not _guess_is_text_attachment(attachment_path, allowed_extensions=allowed):
            continue
        decoded = _decode_attachment_text(attachment_path, max_chars=max_attachment_chars)
        if not decoded:
            continue
        selected_text, selection_mode, selected_count = _select_attachment_snippets(
            decoded,
            max_snippets=max_snippets_per_attachment,
            max_snippet_chars=max_snippet_chars,
            full_attachment_max_chars=full_attachment_max_chars,
            full_attachment_max_lines=full_attachment_max_lines,
        )
        if not selected_text:
            continue
        remaining = max_total_context_chars - total_chars
        clipped_text = selected_text[:remaining].rstrip()
        if not clipped_text:
            break
        rendered_lines.append(f"- attachment: {attachment_name}")
        rendered_lines.append(f"  selection_mode: {selection_mode}")
        rendered_lines.append(f"  content: {json.dumps(clipped_text)}")
        total_chars += len(clipped_text)
        rendered_count += 1
        attachment_summaries.append(
            {
                "attachment_name": attachment_name,
                "selection_mode": selection_mode,
                "snippet_count": selected_count,
                "source_path": str(attachment_path),
            }
        )

    return AttachmentContext(
        rendered_lines=rendered_lines,
        attachments_considered=len(resolved_files),
        attachments_rendered=rendered_count,
        attachment_summaries=attachment_summaries,
    )


def render_ticket_transform_input(
    record: Mapping[str, Any],
    *,
    source_json_path: Path,
    source_root: Path,
    max_comment_chars: int = 8000,
    max_work_note_chars: int = 8000,
    attachment_allowed_extensions: set[str] | None = None,
    max_attachments: int = 3,
    max_attachment_chars: int = 20000,
    max_total_attachment_context_chars: int = 2000,
    max_snippets_per_attachment: int = 3,
    max_snippet_chars: int = 300,
    full_attachment_max_chars: int = 2000,
    full_attachment_max_lines: int = 40,
) -> RenderedTicketInput:
    """Render deterministic prompt input for the ticket transform model."""
    metadata = _as_mapping(record.get("metadata"))
    incident_fields = _as_mapping(record.get("incident_fields"))
    discussions = _as_mapping(record.get("discussions"))
    attachments = _as_list(record.get("attachments"))

    incident_number = _extract_scalar(record, metadata, incident_fields, "incident_number", "number")
    state = _extract_scalar(record, metadata, incident_fields, "state")
    close_code = _extract_scalar(record, metadata, incident_fields, "close_code")
    category = _extract_scalar(record, metadata, incident_fields, "category")
    subcategory = _extract_scalar(record, metadata, incident_fields, "subcategory")
    assignment_group = _extract_scalar(record, metadata, incident_fields, "assignment_group")
    created_on = _extract_scalar(record, metadata, incident_fields, "sys_created_on", "created_on")
    short_description = _extract_scalar(record, metadata, incident_fields, "short_description")
    description = _extract_scalar(record, metadata, incident_fields, "description")

    customer_comments_raw = [
        _format_discussion_line(entry)
        for entry in _as_list(discussions.get("customer_facing_comments"))
        if isinstance(entry, Mapping)
    ]
    customer_comments = [line for line in customer_comments_raw if line]
    customer_comments, truncated_customer_comments = _cap_lines_from_end(
        customer_comments,
        max_comment_chars,
    )

    work_notes_raw = [
        _format_discussion_line(entry)
        for entry in _as_list(discussions.get("internal_work_notes"))
        if isinstance(entry, Mapping)
    ]
    work_notes = [line for line in work_notes_raw if line]
    work_notes, truncated_work_notes = _cap_lines_from_end(work_notes, max_work_note_chars)

    attachment_lines = [
        _format_attachment_line(entry)
        for entry in attachments
        if isinstance(entry, Mapping)
    ]
    attachment_lines = [line for line in attachment_lines if line]

    attachment_context = build_attachment_context(
        record,
        source_json_path=source_json_path,
        source_root=source_root,
        allowed_extensions=attachment_allowed_extensions,
        max_attachments=max_attachments,
        max_attachment_chars=max_attachment_chars,
        max_total_context_chars=max_total_attachment_context_chars,
        max_snippets_per_attachment=max_snippets_per_attachment,
        max_snippet_chars=max_snippet_chars,
        full_attachment_max_chars=full_attachment_max_chars,
        full_attachment_max_lines=full_attachment_max_lines,
    )

    lines = [
        "INCIDENT_METADATA:",
        f"- incident_number: {incident_number}",
        f"- created_on: {created_on}",
        f"- state: {state}",
        f"- close_code: {close_code}",
        f"- category: {category}",
        f"- subcategory: {subcategory}",
        f"- assignment_group: {assignment_group}",
        "",
        "SHORT_DESCRIPTION:",
        short_description or "",
        "",
        "DESCRIPTION:",
        description or "",
        "",
        "CUSTOMER_COMMENTS:",
    ]
    lines.extend(f"- {line}" for line in customer_comments) if customer_comments else lines.append("-")
    if truncated_customer_comments:
        lines.append("- [truncated_to_latest_messages]")
    lines.extend(["", "INTERNAL_WORK_NOTES:"])
    lines.extend(f"- {line}" for line in work_notes) if work_notes else lines.append("-")
    if truncated_work_notes:
        lines.append("- [truncated_to_latest_notes]")
    lines.extend(["", "ATTACHMENT_METADATA:"])
    lines.extend(f"- {line}" for line in attachment_lines) if attachment_lines else lines.append("-")
    lines.extend(["", "ATTACHMENT_TEXT_SNIPPETS:"])
    lines.extend(attachment_context.rendered_lines or ["-"])

    rendered = "\n".join(lines).strip()
    return RenderedTicketInput(
        text=rendered,
        attachment_context=attachment_context,
        prompt_sha256=hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
    )


def build_transform_prompt(rendered_input: str) -> str:
    """Build the user prompt for the transform model."""
    example_input = """INCIDENT_METADATA:
- incident_number: INC0001
- created_on: 2025-01-01 00:00:00
- state: Closed
- close_code: Solved (Permanently)
- category: Software
- subcategory: Python
- assignment_group: Consulting

SHORT_DESCRIPTION:
import fails for numpy

DESCRIPTION:

CUSTOMER_COMMENTS:
- [2025-01-01 01:00:00] USER_A: python import numpy fails in my environment

INTERNAL_WORK_NOTES:
- [2025-01-01 02:00:00] USER_B: rebuilt environment and confirmed missing module path

ATTACHMENT_METADATA:
- env.log (text/plain, 512 bytes)

ATTACHMENT_TEXT_SNIPPETS:
- attachment: env.log
  selection_mode: snippets
  content: "ModuleNotFoundError: No module named 'numpy'" """

    example_output = {
        "incident_summary": (
            "User could not import numpy in a Python environment at NERSC. "
            "The failure appeared during normal environment use and pointed to a missing module path."
        ),
        "resolution_summary": "Support identified a missing module path and rebuilt the environment. Issue resolved.",
        "retrieval_keywords": ["python", "numpy", "import error", "environment rebuild"],
        "evidence_snippets": ["ModuleNotFoundError: No module named 'numpy'"],
    }

    return (
        "Transform the ticket into a compact retrieval-oriented JSON object.\n"
        "Return only JSON with these keys: incident_summary, resolution_summary, "
        "retrieval_keywords, evidence_snippets.\n"
        "Requirements:\n"
        "- Preserve technical signal and resolution details when supported.\n"
        "- PII is not allowed anywhere in the output.\n"
        "- Omit greetings, signatures, usernames, account names, emails, phone numbers, display names, watchlists, and copied login identifiers.\n"
        "- Do not copy quoted user-entered identifiers such as usernames, account names, host-local login names, or password-reset identifiers into the output.\n"
        "- If the source mentions a specific user/account identifier, replace it conceptually with generic wording such as 'the user account' rather than repeating the identifier.\n"
        "- Do not invent unsupported facts.\n"
        "- If the ticket is unresolved or ambiguous, say so briefly in resolution_summary.\n"
        "- incident_summary should usually be 2-4 sentences.\n"
        "- For complex incidents, incident_summary may use up to 6-8 sentences when needed to capture the main debugging path, multiple related failure modes, or important turns in the interaction.\n"
        "- incident_summary should explain what the user was trying to do, what went wrong, and the most important technical findings needed to recognize a similar incident.\n"
        "- Compress repeated back-and-forth into a concise narrative instead of reproducing the transcript.\n"
        "- Keep wording compact and retrieval-oriented.\n"
        "- retrieval_keywords must be short normalized terms.\n"
        "- evidence_snippets must be short technical strings, not paragraphs.\n\n"
        f"Example input:\n{example_input}\n\n"
        f"Example output:\n{json.dumps(example_output, indent=2)}\n\n"
        f"Ticket input:\n{rendered_input}\n"
    )


def extract_json_object(text: str) -> str:
    """Extract a JSON object from a model response."""
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    fenced = JSON_FENCE_PATTERN.search(stripped)
    if fenced:
        return fenced.group(1).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1].strip()
    raise ValueError("Model response did not contain a JSON object")


def normalize_derived_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize model output into the expected schema shape."""
    normalized: dict[str, Any] = {}
    for key in (
        "incident_summary",
        "resolution_summary",
    ):
        normalized[key] = _stringify(payload.get(key))
    for key in ("retrieval_keywords", "evidence_snippets"):
        values = payload.get(key)
        if not isinstance(values, list):
            normalized[key] = []
            continue
        items = [_stringify(item) for item in values]
        normalized[key] = [item for item in items if item]
    return normalized


def coerce_derived_payload(
    payload: Mapping[str, Any],
    *,
    limits: DerivedFieldLimits,
) -> dict[str, Any]:
    """Apply deterministic, auditable coercions that do not rewrite semantic content."""
    normalized = normalize_derived_payload(payload)

    keywords = normalized.get("retrieval_keywords")
    if isinstance(keywords, list):
        normalized["retrieval_keywords"] = [
            _stringify(item) for item in keywords if _stringify(item)
        ][: limits.max_keywords]

    snippets = normalized.get("evidence_snippets")
    if isinstance(snippets, list):
        normalized["evidence_snippets"] = [
            _stringify(item) for item in snippets if _stringify(item)
        ][: limits.max_evidence_snippets]

    return normalized


def contains_email_like_pii(text: str) -> bool:
    """Return True for plausible email addresses, excluding common linker-symbol false positives."""
    for match in EMAIL_PATTERN.finditer(text):
        token = match.group(0)
        if LIB_SYMBOL_EMAIL_FALSE_POSITIVE_PATTERN.search(token):
            continue
        return True
    return False


def contains_phone_like_pii(text: str) -> bool:
    """Return True for plausible phone numbers, excluding generic numeric identifiers."""
    return PHONE_PATTERN.search(text) is not None


def find_derived_payload_violations(
    payload: Mapping[str, Any],
    *,
    limits: DerivedFieldLimits,
) -> list[str]:
    """Return validation errors for a normalized derived payload."""
    violations: list[str] = []

    def _require_non_empty(field: str) -> str:
        value = _stringify(payload.get(field))
        if not value:
            violations.append(f"{field} is required")
        return value

    incident_summary = _require_non_empty("incident_summary")
    resolution_summary = _require_non_empty("resolution_summary")
    retrieval_keywords = payload.get("retrieval_keywords")
    evidence_snippets = payload.get("evidence_snippets")

    if incident_summary and len(incident_summary) > limits.incident_summary_chars:
        violations.append(
            f"incident_summary exceeds {limits.incident_summary_chars} chars"
        )
    if resolution_summary and len(resolution_summary) > limits.resolution_summary_chars:
        violations.append(
            f"resolution_summary exceeds {limits.resolution_summary_chars} chars"
        )

    if not isinstance(retrieval_keywords, list) or not retrieval_keywords:
        violations.append("retrieval_keywords must contain at least one item")
    else:
        if len(retrieval_keywords) > limits.max_keywords:
            violations.append(f"retrieval_keywords exceeds {limits.max_keywords} items")
        for item in retrieval_keywords:
            if not isinstance(item, str) or not item.strip():
                violations.append("retrieval_keywords contains empty item")
                break

    if evidence_snippets is not None:
        if not isinstance(evidence_snippets, list):
            violations.append("evidence_snippets must be a list")
        elif len(evidence_snippets) > limits.max_evidence_snippets:
            violations.append(
                f"evidence_snippets exceeds {limits.max_evidence_snippets} items"
            )

    for field in ("incident_summary", "resolution_summary"):
        value = _stringify(payload.get(field))
        if contains_email_like_pii(value):
            violations.append(f"{field} contains email address")
        if contains_phone_like_pii(value):
            violations.append(f"{field} contains phone number")

    for list_field in ("retrieval_keywords", "evidence_snippets"):
        values = payload.get(list_field)
        if not isinstance(values, list):
            continue
        for item in values:
            text = _stringify(item)
            if contains_email_like_pii(text):
                violations.append(f"{list_field} contains email address")
                break
            if contains_phone_like_pii(text):
                violations.append(f"{list_field} contains phone number")
                break

    return violations


def build_repair_prompt(rendered_input: str, raw_response: str, violations: list[str]) -> str:
    """Build a repair prompt for invalid model output."""
    return (
        "Your previous response did not satisfy the required JSON schema.\n"
        "Return only a corrected JSON object with keys: incident_summary, "
        "resolution_summary, retrieval_keywords, evidence_snippets.\n"
        "Repair instructions:\n"
        "- If a summary contains any email address, phone number, username, account name, login identifier, or other PII, rewrite the sentence with generic wording instead of copying the identifier.\n"
        "- If any retrieval_keywords item or evidence_snippets item contains an email address, phone number, username, account name, login identifier, or other PII, remove that item entirely rather than paraphrasing it.\n"
        "- If retrieval_keywords has more than the allowed number of items, keep only the most useful normalized terms.\n"
        "- If evidence_snippets has more than the allowed number of items, keep only the most useful short technical strings.\n"
        "- Do not repeat the previous invalid output unchanged.\n"
        f"Validation errors:\n- " + "\n- ".join(violations) + "\n\n"
        f"Original ticket input:\n{rendered_input}\n\n"
        f"Previous invalid response:\n{raw_response}\n"
    )


def render_derived_retrieval_document(payload: Mapping[str, Any]) -> str:
    """Render the retrieval document from a validated derived payload."""
    incident_summary = _stringify(payload.get("incident_summary"))
    resolution_summary = _stringify(payload.get("resolution_summary"))
    retrieval_keywords = payload.get("retrieval_keywords")
    evidence_snippets = payload.get("evidence_snippets")

    lines = [
        "INCIDENT_SUMMARY:",
        incident_summary,
        "",
        "RESOLUTION_SUMMARY:",
        resolution_summary,
        "",
        "RETRIEVAL_KEYWORDS:",
    ]
    if isinstance(retrieval_keywords, list) and retrieval_keywords:
        lines.extend(f"- {_stringify(item)}" for item in retrieval_keywords if _stringify(item))
    else:
        lines.append("-")
    lines.extend(["", "EVIDENCE_SNIPPETS:"])
    if isinstance(evidence_snippets, list) and evidence_snippets:
        lines.extend(f"- {_stringify(item)}" for item in evidence_snippets if _stringify(item))
    else:
        lines.append("-")
    return "\n".join(lines).strip()


def derived_record_doc_id(payload: Mapping[str, Any]) -> str:
    """Return a stable Chroma doc id for one derived ticket record."""
    incident_number = _stringify(payload.get("incident_number"))
    if incident_number:
        return f"{incident_number}::derived"
    source_json_path = _stringify(payload.get("source_json_path"))
    if source_json_path:
        return f"{Path(source_json_path).stem}::derived"
    raise ValueError("Derived ticket record is missing incident_number/source_json_path")


def build_derived_ticket_document(payload: Mapping[str, Any]) -> TicketDocument:
    """Convert one derived ticket record into a Chroma-ready document."""
    text = render_derived_retrieval_document(payload)
    metadata: dict[str, Any] = {
        "record_type": "derived_ticket",
        "incident_number": _stringify(payload.get("incident_number")),
        "sys_id": _stringify(payload.get("sys_id")),
        "sys_created_on": _stringify(payload.get("sys_created_on")),
        "assignment_group": _stringify(payload.get("assignment_group")),
        "category": _stringify(payload.get("category")),
        "subcategory": _stringify(payload.get("subcategory")),
        "state": _stringify(payload.get("state")),
        "close_code": _stringify(payload.get("close_code")),
        "schema_version": _stringify(payload.get("schema_version")),
        "source_json_path": _stringify(payload.get("source_json_path")),
    }
    return TicketDocument(
        doc_id=derived_record_doc_id(payload),
        text=text,
        metadata=metadata,
    )


def render_derived_ticket_markdown(payload: Mapping[str, Any]) -> str:
    """Render one derived ticket record as a readable Markdown file."""
    lines = [
        f"# {_stringify(payload.get('incident_number')) or 'Derived Ticket'}",
        "",
        "## Metadata",
        "",
        f"- incident_number: {_stringify(payload.get('incident_number')) or '-'}",
        f"- created_on: {_stringify(payload.get('sys_created_on')) or '-'}",
        f"- state: {_stringify(payload.get('state')) or '-'}",
        f"- close_code: {_stringify(payload.get('close_code')) or '-'}",
        f"- category: {_stringify(payload.get('category')) or '-'}",
        f"- subcategory: {_stringify(payload.get('subcategory')) or '-'}",
        f"- assignment_group: {_stringify(payload.get('assignment_group')) or '-'}",
        "",
        "## Incident Summary",
        "",
        _stringify(payload.get("incident_summary")) or "-",
        "",
        "## Resolution Summary",
        "",
        _stringify(payload.get("resolution_summary")) or "-",
        "",
        "## Retrieval Keywords",
        "",
    ]
    retrieval_keywords = payload.get("retrieval_keywords")
    if isinstance(retrieval_keywords, list) and retrieval_keywords:
        lines.extend(
            f"- {_stringify(item)}" for item in retrieval_keywords if _stringify(item)
        )
    else:
        lines.append("-")

    lines.extend(["", "## Evidence Snippets", ""])
    evidence_snippets = payload.get("evidence_snippets")
    if isinstance(evidence_snippets, list) and evidence_snippets:
        lines.extend(
            f"- {_stringify(item)}" for item in evidence_snippets if _stringify(item)
        )
    else:
        lines.append("-")

    source_json_path = _stringify(payload.get("source_json_path"))
    if source_json_path:
        lines.extend(["", "## Provenance", "", f"- source_json_path: {source_json_path}"])
    return "\n".join(lines).strip() + "\n"


def derived_ticket_materialized_relpath(payload: Mapping[str, Any]) -> Path:
    """Return a sharded relative Markdown path for one derived ticket record."""
    incident_number = _stringify(payload.get("incident_number"))
    if incident_number.startswith("INC") and len(incident_number) >= 10:
        digits = incident_number[3:]
        if digits.isdigit():
            remainder = digits[3:]
            if len(remainder) >= 4:
                return Path(incident_number[:6]) / remainder[:2] / f"{remainder[2:]}.md"
    fallback = incident_number or derived_record_doc_id(payload).replace("::derived", "")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", fallback).strip("_") or "derived_ticket"
    return Path(f"{safe}.md")
