#!/usr/bin/env python3
"""CLI utility to summarize the contents of a ChromaDB database."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import chromadb


def summarize_collections(client: chromadb.Client, indent: str = "") -> None:
    """Print a summary of collections and their metadata."""
    collections = client.list_collections()
    print(f"Found {len(collections)} collections")
    for coll in collections:
        # Some collection objects return raw metadata dicts
        metadata = coll.metadata or {}
        try:
            count = coll.count()
        except Exception:
            count = "?"
        print(f"{indent}- {coll.name} (count={count}) metadata={metadata}")


def list_collection(coll: chromadb.Collection, indent: str = "") -> None:
    """List all items in ``coll`` along with their metadata."""
    results = coll.get(include=["documents", "metadatas", "ids"])
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    print(f"{indent}Collection '{coll.name}' contains {len(ids)} items")
    for idx, (id_, doc, meta) in enumerate(zip(ids, documents, metadatas), start=1):
        snippet = doc if doc is None or len(doc) <= 80 else doc[:77] + "..."
        print(f"{indent}  {idx}. id={id_}")
        if doc is not None:
            print(f"{indent}     doc={snippet}")
        print(f"{indent}     metadata={meta}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize collections and optionally list their contents"
    )
    parser.add_argument(
        "persist_dir",
        type=Path,
        help="Directory containing the persisted ChromaDB",
    )
    parser.add_argument(
        "--collection",
        help="Name of a collection to list its contents",
    )
    parser.add_argument(
        "--list-all",
        action="store_true",
        help="List contents of every collection",
    )
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=str(args.persist_dir))

    if args.collection or args.list_all:
        cols: Iterable[chromadb.Collection]
        if args.list_all:
            cols = client.list_collections()
        else:
            cols = [client.get_collection(args.collection)]
        for coll in cols:
            list_collection(coll)
            print()
    else:
        summarize_collections(client)


if __name__ == "__main__":
    main()
