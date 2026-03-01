#!/usr/bin/env python3
"""Filter ServiceNow ticket corpus and materialize a copied filtered subset."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import shutil
from typing import Any, Iterable, Mapping

from athos.utils.ticket_ingest import (
    compute_corpus_fingerprint,
    evaluate_ticket_filter_reason,
    iter_ticket_json_files,
    load_ticket_json,
    write_manifest,
)


logger = logging.getLogger(__name__)

DEFAULT_MIN_CREATED_DATE = "2023-01-01"
DEFAULT_EXCLUDE_CONTACT_TYPES = ("Staff Initiated", "System Alert Auto Generated")
STRICT_INCLUDE_CONTACT_TYPES = ("Email", "User Web Interface", "Phone", "In Person")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter ServiceNow ticket JSON corpus and copy selected incidents + attachments"
    )
    parser.add_argument("source_path", help="Path to ticket export root")
    parser.add_argument(
        "--output-root",
        required=True,
        help="Destination root for copied filtered corpus",
    )
    parser.add_argument(
        "--mode",
        choices=("balanced", "user_support_strict", "full_corpus"),
        default="balanced",
        help="Filter policy mode",
    )
    parser.add_argument(
        "--min-created-date",
        help="Exclude tickets created before YYYY-MM-DD",
    )
    parser.add_argument(
        "--exclude-contact-type",
        action="append",
        default=None,
        help="Exclude this contact type (repeatable)",
    )
    parser.add_argument(
        "--include-contact-type",
        action="append",
        default=None,
        help="Only include these contact types (repeatable)",
    )
    parser.add_argument(
        "--exclude-created-by-regex",
        help="Regex for creators to exclude",
    )
    parser.add_argument(
        "--exclude-assignment-group-regex",
        help="Regex for assignment groups to exclude",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max number of kept tickets to process (applied after filters)",
    )
    parser.add_argument(
        "--manifest-out",
        help="Path to write filtered corpus manifest JSON (default: <output-root>/filter_manifest.json)",
    )
    parser.add_argument(
        "--allow-file-errors",
        action="store_true",
        help="Exit successfully even when some ticket files fail to parse/process",
    )
    parser.add_argument(
        "--allow-missing-attachments",
        action="store_true",
        help="Exit successfully even when attachment references cannot be resolved",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate filters and attachment resolution, but do not copy files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity",
    )
    return parser.parse_args()


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    logging.basicConfig(level=level)


def _normalize_type_set(values: list[str] | tuple[str, ...] | None) -> set[str]:
    if not values:
        return set()
    return {item.strip() for item in values if item and item.strip()}


def _resolve_mode_filters(args: argparse.Namespace) -> tuple[str | None, set[str], set[str]]:
    if args.mode == "full_corpus":
        min_created_date = None
        include_contact_types: set[str] = set()
        exclude_contact_types: set[str] = set()
    elif args.mode == "user_support_strict":
        min_created_date = DEFAULT_MIN_CREATED_DATE
        include_contact_types = set(STRICT_INCLUDE_CONTACT_TYPES)
        exclude_contact_types = set(DEFAULT_EXCLUDE_CONTACT_TYPES)
    else:  # balanced
        min_created_date = DEFAULT_MIN_CREATED_DATE
        include_contact_types = set()
        exclude_contact_types = set(DEFAULT_EXCLUDE_CONTACT_TYPES)

    if args.min_created_date is not None:
        min_created_date = args.min_created_date
    if args.include_contact_type is not None:
        include_contact_types = _normalize_type_set(args.include_contact_type)
    if args.exclude_contact_type is not None:
        exclude_contact_types = _normalize_type_set(args.exclude_contact_type)
    return min_created_date, include_contact_types, exclude_contact_types


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        stable = value.get("value")
        if isinstance(stable, str) and stable.strip():
            return stable.strip()
        display = value.get("display_value")
        if isinstance(display, str) and display.strip():
            return display.strip()
    return ""


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
    for child in sorted(ticket_file.parent.iterdir()):
        if not child.is_dir():
            continue
        name_lower = child.name.lower()
        if name_lower.endswith("_attachements") or name_lower.endswith("_attachments"):
            yield child


def _resolve_attachment_candidate(
    local_path: str,
    *,
    source_root: Path,
) -> Path | None:
    candidate = Path(local_path)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None

    joined = (source_root / candidate).resolve()
    if joined.exists():
        return joined

    parts = list(candidate.parts)
    if parts and parts[0] == source_root.name:
        stripped = (source_root / Path(*parts[1:])).resolve()
        if stripped.exists():
            return stripped
    return None


def _relative_output_path(path: Path, *, source_root: Path, incident_rel: Path) -> Path:
    try:
        return path.resolve().relative_to(source_root.resolve())
    except ValueError:
        return incident_rel.parent / "_external_attachments" / path.name


def _copy_file(src: Path, dst: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    source_root = Path(args.source_path)
    if not source_root.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_root}")
    source_root = source_root.resolve()

    output_root = Path(args.output_root).resolve()
    manifest_path = (
        Path(args.manifest_out).resolve()
        if args.manifest_out
        else output_root / "filter_manifest.json"
    )

    min_created_date_str, include_contact_types, exclude_contact_types = _resolve_mode_filters(args)
    min_created_date = (
        datetime.strptime(min_created_date_str, "%Y-%m-%d").date()
        if min_created_date_str
        else None
    )
    created_by_pattern = (
        re.compile(args.exclude_created_by_regex) if args.exclude_created_by_regex else None
    )
    assignment_group_pattern = (
        re.compile(args.exclude_assignment_group_regex)
        if args.exclude_assignment_group_regex
        else None
    )

    ticket_files = list(iter_ticket_json_files(source_root))
    filtered_counts: Counter[str] = Counter()
    selected_files: list[Path] = []
    error_count = 0
    attachment_refs_total = 0
    attachment_files_copied = 0
    attachment_missing_count = 0

    if not args.dry_run:
        output_root.mkdir(parents=True, exist_ok=True)

    copied_destinations: set[Path] = set()
    for ticket_file in ticket_files:
        if args.limit is not None and len(selected_files) >= args.limit:
            break

        try:
            payload = load_ticket_json(ticket_file)
            filter_reason = evaluate_ticket_filter_reason(
                payload,
                min_created_date=min_created_date,
                include_contact_types=include_contact_types,
                exclude_contact_types=exclude_contact_types,
                exclude_created_by_pattern=created_by_pattern,
                exclude_assignment_group_pattern=assignment_group_pattern,
            )
            if filter_reason:
                filtered_counts[filter_reason] += 1
                continue

            selected_files.append(ticket_file)
            incident_rel = ticket_file.relative_to(source_root)
            incident_dst = output_root / incident_rel
            if incident_dst not in copied_destinations:
                _copy_file(ticket_file, incident_dst, dry_run=args.dry_run)
                copied_destinations.add(incident_dst)

            attachment_sources: set[Path] = set()
            for local_path in _extract_attachment_local_paths(payload):
                attachment_refs_total += 1
                resolved = _resolve_attachment_candidate(local_path, source_root=source_root)
                if resolved is None or not resolved.is_file():
                    attachment_missing_count += 1
                    logger.warning("Unresolved attachment local_path=%s for %s", local_path, ticket_file)
                    continue
                attachment_sources.add(resolved)

            for attachment_dir in _iter_attachment_dir_candidates(ticket_file):
                for file_path in sorted(attachment_dir.rglob("*")):
                    if file_path.is_file():
                        attachment_sources.add(file_path.resolve())

            for attachment_src in sorted(attachment_sources):
                attachment_rel = _relative_output_path(
                    attachment_src,
                    source_root=source_root,
                    incident_rel=incident_rel,
                )
                attachment_dst = output_root / attachment_rel
                if attachment_dst in copied_destinations:
                    continue
                _copy_file(attachment_src, attachment_dst, dry_run=args.dry_run)
                copied_destinations.add(attachment_dst)
                attachment_files_copied += 1
        except Exception:
            error_count += 1
            logger.exception("Failed to process %s", ticket_file)

    materialized_selected_files = [output_root / path.relative_to(source_root) for path in selected_files]
    if args.dry_run:
        fingerprint = compute_corpus_fingerprint(source_root, selected_files)
    else:
        fingerprint = compute_corpus_fingerprint(output_root, materialized_selected_files)
    selected_rel_paths = [str(path.relative_to(source_root)) for path in selected_files]
    manifest = {
        "schema_version": "athos.ticket_filter_manifest.v1",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_path": str(output_root),
        "upstream_source_path": str(source_root),
        "output_root": str(output_root),
        "config": {
            "mode": args.mode,
            "min_created_date": min_created_date_str,
            "include_contact_types": sorted(include_contact_types),
            "exclude_contact_types": sorted(exclude_contact_types),
            "exclude_created_by_regex": args.exclude_created_by_regex,
            "exclude_assignment_group_regex": args.exclude_assignment_group_regex,
            "limit": args.limit,
            "dry_run": args.dry_run,
        },
        "counts": {
            "input_files": len(ticket_files),
            "selected_files": len(selected_files),
            "filtered": int(sum(filtered_counts.values())),
            "filtered_by_reason": dict(filtered_counts),
            "errors": error_count,
            "attachment_references": attachment_refs_total,
            "attachments_copied": attachment_files_copied,
            "attachments_missing": attachment_missing_count,
        },
        "corpus_fingerprint": {
            "file_count": fingerprint.file_count,
            "sha256": fingerprint.sha256,
        },
        "selected_files": selected_rel_paths,
    }

    write_manifest(manifest_path, manifest)

    print(
        f"selected_files={len(selected_files)} "
        f"filtered={sum(filtered_counts.values())} "
        f"attachments_copied={attachment_files_copied} "
        f"attachments_missing={attachment_missing_count} "
        f"errors={error_count}"
    )
    print(f"manifest={manifest_path}")

    if attachment_missing_count and not args.allow_missing_attachments:
        raise RuntimeError(
            "Encountered missing attachment references; rerun with --allow-missing-attachments to continue"
        )
    if error_count and not args.allow_file_errors:
        raise RuntimeError(
            f"Encountered {error_count} file processing errors; rerun with --allow-file-errors to continue"
        )


if __name__ == "__main__":
    main()
