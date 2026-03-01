#!/usr/bin/env python3
"""CLI for building a Chroma collection from ServiceNow ticket JSON files."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import subprocess
from typing import Any

from athos.utils.ticket_ingest import (
    build_full_incident_document,
    compute_corpus_fingerprint,
    load_ticket_json,
    write_manifest,
)


logger = logging.getLogger(__name__)

def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a ChromaDB collection from a selected ticket corpus manifest"
    )
    parser.add_argument(
        "--selected-corpus-manifest",
        required=True,
        help="Path to stage-1 filter manifest with selected_files + source_path",
    )
    parser.add_argument("--persist-dir", default="chroma", help="Directory to store ChromaDB data")
    parser.add_argument(
        "--collection-name",
        default="servicenow_tickets_v0",
        help="Name of the Chroma collection",
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
        "--batch-size",
        type=_positive_int,
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
        "--allow-file-errors",
        action="store_true",
        help="Exit successfully even when some ticket files fail to process",
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


def _load_selected_corpus_manifest(path: Path) -> tuple[Path, list[Path]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object manifest at {path}")

    source_path = payload.get("source_path")
    selected_files = payload.get("selected_files")
    config = payload.get("config")
    if not isinstance(source_path, str) or not source_path.strip():
        raise ValueError(f"Manifest missing string source_path: {path}")
    if not isinstance(selected_files, list):
        raise ValueError(f"Manifest missing selected_files list: {path}")
    if isinstance(config, dict) and config.get("materialized") is False:
        raise ValueError(
            "Selected corpus manifest indicates dry-run/non-materialized output; "
            "rerun filter stage without --dry-run before ingestion"
        )

    source_root = Path(source_path).resolve()
    ticket_files: list[Path] = []
    for item in selected_files:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Manifest selected_files entries must be non-empty strings: {path}")
        candidate = (source_root / Path(item)).resolve()
        try:
            candidate.relative_to(source_root)
        except ValueError as exc:
            raise ValueError(
                f"Manifest selected_files entry escapes source_path: {item}"
            ) from exc
        if not candidate.exists():
            raise FileNotFoundError(
                f"Manifest-selected ticket file does not exist under source_path: {candidate}"
            )
        ticket_files.append(candidate)
    return source_root, ticket_files


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    selected_manifest_path = Path(args.selected_corpus_manifest).resolve()
    source_root, ticket_files = _load_selected_corpus_manifest(selected_manifest_path)
    input_source_mode = "selected_corpus_manifest"

    documents: list[tuple[str, str, dict[str, object]]] = []
    error_count = 0
    truncated_comment_docs = 0
    truncated_work_note_docs = 0
    chunked_tickets = 0
    kept_tickets = 0
    kept_ticket_files: list[Path] = []
    for ticket_file in ticket_files:
        try:
            payload = load_ticket_json(ticket_file)

            kept_tickets += 1
            kept_ticket_files.append(ticket_file)
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

    fingerprint = compute_corpus_fingerprint(source_root, kept_ticket_files)
    resolved_documents, duplicate_doc_ids = _resolve_duplicate_policy(documents, args.on_duplicate_id)
    manifest = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_path": str(source_root.resolve()),
        "input_source_mode": input_source_mode,
        "selected_corpus_manifest": str(selected_manifest_path) if selected_manifest_path else None,
        "collection_name": args.collection_name,
        "persist_dir": str(Path(args.persist_dir)),
        "dry_run": args.dry_run,
        "git_sha": _get_git_sha(),
        "corpus_fingerprint": {
            "file_count": fingerprint.file_count,
            "sha256": fingerprint.sha256,
        },
        "config": {
            "max_comment_chars": args.max_comment_chars,
            "max_work_note_chars": args.max_work_note_chars,
            "max_incident_chars": args.max_incident_chars,
            "batch_size": args.batch_size,
            "on_duplicate_id": args.on_duplicate_id,
        },
        "counts": {
            "input_files": len(ticket_files),
            "kept_tickets": kept_tickets,
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
            f"chunked_tickets={chunked_tickets} "
            f"truncated_comment_docs={truncated_comment_docs} "
            f"truncated_work_note_docs={truncated_work_note_docs} "
            f"duplicate_doc_ids={duplicate_doc_ids} "
            f"errors={error_count}"
        )
        if args.manifest_out:
            write_manifest(Path(args.manifest_out), manifest)
        if error_count and not args.allow_file_errors:
            raise RuntimeError(
                f"Encountered {error_count} file processing errors; rerun with --allow-file-errors to continue"
            )
        return

    if error_count and not args.allow_file_errors:
        if args.manifest_out:
            write_manifest(Path(args.manifest_out), manifest)
        raise RuntimeError(
            f"Encountered {error_count} file processing errors; rerun with --allow-file-errors to continue"
        )

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
        f"chunked_tickets={chunked_tickets} "
        f"truncated_comment_docs={truncated_comment_docs} "
        f"truncated_work_note_docs={truncated_work_note_docs} "
        f"duplicate_doc_ids={duplicate_doc_ids} "
        f"errors={error_count}"
    )
    if args.manifest_out:
        write_manifest(Path(args.manifest_out), manifest)


if __name__ == "__main__":
    main()
