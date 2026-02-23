#!/usr/bin/env python3
"""CLI for building a Chroma collection from ServiceNow ticket JSON files."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from athos.utils.ticket_ingest import (
    build_full_incident_document,
    iter_ticket_json_files,
    load_ticket_json,
)


logger = logging.getLogger(__name__)


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
        "--max-incident-chars",
        type=int,
        default=40000,
        help="Maximum chars per full incident document before chunk fallback",
    )
    parser.add_argument("--limit", type=int, help="Max number of JSON files to process")
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


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    source_root = Path(args.source_path)
    if not source_root.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_root}")

    ticket_files = list(iter_ticket_json_files(source_root))
    if args.limit is not None:
        ticket_files = ticket_files[: args.limit]

    documents: list[tuple[str, str, dict[str, object]]] = []
    error_count = 0
    for ticket_file in ticket_files:
        try:
            payload = load_ticket_json(ticket_file)
            for doc in build_full_incident_document(
                payload,
                source_json_path=ticket_file,
                max_chars=args.max_incident_chars,
            ):
                documents.append((doc.doc_id, doc.text, doc.metadata))
        except Exception:  # pragma: no cover - exercised by CLI
            error_count += 1
            logger.exception("Failed to process %s", ticket_file)

    if args.dry_run:
        print(
            "dry_run=true "
            f"files={len(ticket_files)} documents={len(documents)} errors={error_count}"
        )
        return

    import chromadb

    client = chromadb.PersistentClient(path=str(Path(args.persist_dir)))
    collection = client.get_or_create_collection(name=args.collection_name)
    if documents:
        ids = [item[0] for item in documents]
        texts = [item[1] for item in documents]
        metadatas = [item[2] for item in documents]
        collection.add(ids=ids, documents=texts, metadatas=metadatas)

    print(
        f"collection={args.collection_name} files={len(ticket_files)} "
        f"documents={len(documents)} errors={error_count}"
    )


if __name__ == "__main__":
    main()
