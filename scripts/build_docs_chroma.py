#!/usr/bin/env python3
"""CLI for ingesting markdown docs into a ChromaDB collection."""

import argparse
import logging
from pathlib import Path

from athos.utils.chroma_ingest import build_collection


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a ChromaDB collection from markdown docs")
    parser.add_argument("docs_path", help="Path to directory containing markdown files")
    parser.add_argument("--persist-dir", default="chroma", help="Directory to store ChromaDB data")
    parser.add_argument("--collection-name", default="docs", help="Name of the Chroma collection")
    parser.add_argument(
        "--chunk-size", type=int, default=15000, help="Chunk size threshold in characters"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity",
    )
    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose >= 2:
        log_level = logging.DEBUG
    elif args.verbose == 1:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)

    build_collection(Path(args.docs_path), Path(args.persist_dir), args.collection_name, args.chunk_size)


if __name__ == "__main__":
    main()
