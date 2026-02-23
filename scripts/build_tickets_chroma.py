#!/usr/bin/env python3
"""CLI for building a Chroma collection from ServiceNow ticket JSON files."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import logging
from pathlib import Path
import re
import subprocess
from typing import Any

from athos.utils.ticket_ingest import (
    build_full_incident_document,
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
    parser = argparse.ArgumentParser(description="Build a ChromaDB collection from ticket JSON files")
    parser.add_argument("source_path", help="Path to ticket export root")
    parser.add_argument("--persist-dir", default="chroma", help="Directory to store ChromaDB data")
    parser.add_argument(
        "--collection-name",
        default="servicenow_tickets_v0",
        help="Name of the Chroma collection",
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
        "--max-comment-chars",
        type=int,
        default=12000,
        help="Maximum chars kept across flattened customer comments",
    )
    parser.add_argument(
        "--max-work-note-chars",
        type=int,
        default=12000,
        help="Maximum chars kept across flattened internal work notes",
    )
    parser.add_argument(
        "--max-incident-chars",
        type=int,
        default=40000,
        help="Maximum chars per full incident document before chunk fallback",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max number of kept tickets to process (applied after filters)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of documents to write per Chroma batch",
    )
    parser.add_argument(
        "--on-duplicate-id",
        choices=("error", "skip", "upsert"),
        default="error",
        help="Behavior when duplicate doc IDs are produced during a run",
    )
    parser.add_argument(
        "--manifest-out",
        help="Path to write run manifest JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse/normalize and report counts only; do not write Chroma",
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


def _resolve_duplicate_policy(
    documents: list[tuple[str, str, dict[str, object]]],
    policy: str,
) -> tuple[list[tuple[str, str, dict[str, object]]], int]:
    if policy == "error":
        seen: set[str] = set()
        for doc_id, _, _ in documents:
            if doc_id in seen:
                raise ValueError(f"Duplicate document id encountered: {doc_id}")
            seen.add(doc_id)
        return documents, 0

    deduped: dict[str, tuple[str, str, dict[str, object]]] = {}
    duplicate_count = 0
    for doc_id, doc_text, doc_meta in documents:
        if doc_id in deduped:
            duplicate_count += 1
            if policy == "skip":
                continue
        deduped[doc_id] = (doc_id, doc_text, doc_meta)
    return list(deduped.values()), duplicate_count


def _write_in_batches(
    collection: Any,
    documents: list[tuple[str, str, dict[str, object]]],
    *,
    batch_size: int,
    upsert: bool,
) -> int:
    written = 0
    for idx in range(0, len(documents), batch_size):
        batch = documents[idx : idx + batch_size]
        ids = [item[0] for item in batch]
        texts = [item[1] for item in batch]
        metadatas = [item[2] for item in batch]
        if upsert:
            collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        else:
            collection.add(ids=ids, documents=texts, metadatas=metadatas)
        written += len(batch)
    return written


def _get_git_sha() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    sha = completed.stdout.strip()
    return sha or None


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    source_root = Path(args.source_path)
    if not source_root.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_root}")

    ticket_files = list(iter_ticket_json_files(source_root))

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

    documents: list[tuple[str, str, dict[str, object]]] = []
    error_count = 0
    filtered_counts: Counter[str] = Counter()
    truncated_comment_docs = 0
    truncated_work_note_docs = 0
    chunked_tickets = 0
    kept_tickets = 0
    for ticket_file in ticket_files:
        if args.limit is not None and kept_tickets >= args.limit:
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

            kept_tickets += 1
            ticket_docs = build_full_incident_document(
                payload,
                source_json_path=ticket_file,
                max_chars=args.max_incident_chars,
                max_comment_chars=args.max_comment_chars,
                max_work_note_chars=args.max_work_note_chars,
            )
            if ticket_docs and len(ticket_docs) > 1:
                chunked_tickets += 1

            for doc in ticket_docs:
                if doc.metadata.get("truncated_comments"):
                    truncated_comment_docs += 1
                if doc.metadata.get("truncated_work_notes"):
                    truncated_work_note_docs += 1
                documents.append((doc.doc_id, doc.text, doc.metadata))
        except Exception:  # pragma: no cover - exercised by CLI
            error_count += 1
            logger.exception("Failed to process %s", ticket_file)

    fingerprint = compute_corpus_fingerprint(source_root, ticket_files)
    resolved_documents, duplicate_doc_ids = _resolve_duplicate_policy(documents, args.on_duplicate_id)
    manifest = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_path": str(source_root.resolve()),
        "collection_name": args.collection_name,
        "persist_dir": str(Path(args.persist_dir)),
        "dry_run": args.dry_run,
        "git_sha": _get_git_sha(),
        "corpus_fingerprint": {
            "file_count": fingerprint.file_count,
            "sha256": fingerprint.sha256,
        },
        "config": {
            "mode": args.mode,
            "min_created_date": min_created_date_str,
            "include_contact_types": sorted(include_contact_types),
            "exclude_contact_types": sorted(exclude_contact_types),
            "exclude_created_by_regex": args.exclude_created_by_regex,
            "exclude_assignment_group_regex": args.exclude_assignment_group_regex,
            "max_comment_chars": args.max_comment_chars,
            "max_work_note_chars": args.max_work_note_chars,
            "max_incident_chars": args.max_incident_chars,
            "limit": args.limit,
            "batch_size": args.batch_size,
            "on_duplicate_id": args.on_duplicate_id,
        },
        "counts": {
            "input_files": len(ticket_files),
            "kept_tickets": kept_tickets,
            "filtered": int(sum(filtered_counts.values())),
            "filtered_by_reason": dict(filtered_counts),
            "documents_before_dedup": len(documents),
            "documents_written": len(resolved_documents),
            "duplicate_doc_ids_in_run": duplicate_doc_ids,
            "chunked_tickets": chunked_tickets,
            "truncated_comment_docs": truncated_comment_docs,
            "truncated_work_note_docs": truncated_work_note_docs,
            "errors": error_count,
        },
    }

    if args.dry_run:
        print(
            "dry_run=true "
            f"files={len(ticket_files)} "
            f"documents={len(resolved_documents)} "
            f"filtered={sum(filtered_counts.values())} "
            f"chunked_tickets={chunked_tickets} "
            f"truncated_comment_docs={truncated_comment_docs} "
            f"truncated_work_note_docs={truncated_work_note_docs} "
            f"duplicate_doc_ids={duplicate_doc_ids} "
            f"errors={error_count}"
        )
        if filtered_counts:
            print(f"filtered_by_reason={dict(filtered_counts)}")
        if args.manifest_out:
            write_manifest(Path(args.manifest_out), manifest)
        return

    import chromadb

    client = chromadb.PersistentClient(path=str(Path(args.persist_dir)))
    collection = client.get_or_create_collection(name=args.collection_name)
    if resolved_documents:
        _write_in_batches(
            collection,
            resolved_documents,
            batch_size=args.batch_size,
            upsert=args.on_duplicate_id == "upsert",
        )

    print(
        f"collection={args.collection_name} "
        f"files={len(ticket_files)} "
        f"documents={len(resolved_documents)} "
        f"filtered={sum(filtered_counts.values())} "
        f"chunked_tickets={chunked_tickets} "
        f"truncated_comment_docs={truncated_comment_docs} "
        f"truncated_work_note_docs={truncated_work_note_docs} "
        f"duplicate_doc_ids={duplicate_doc_ids} "
        f"errors={error_count}"
    )
    if filtered_counts:
        print(f"filtered_by_reason={dict(filtered_counts)}")
    if args.manifest_out:
        write_manifest(Path(args.manifest_out), manifest)


if __name__ == "__main__":
    main()
