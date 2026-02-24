#!/usr/bin/env python3
"""Run retrieval smoke queries against a ticket Chroma collection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import chromadb


DEFAULT_QUERIES = [
    "python package import error on login node",
    "quota exceeded in home directory",
    "gpu job failure slurm",
    "cannot connect ssh to perlmutter",
    "jupyter notebook failed to start",
]


def _load_queries(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_QUERIES)
    lines = path.read_text(encoding="utf-8").splitlines()
    queries = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    if not queries:
        raise ValueError(f"No queries loaded from {path}")
    return queries


def _format_row(rank: int, doc_id: str, metadata: dict[str, Any] | None) -> str:
    meta = metadata or {}
    incident = meta.get("incident_number", "")
    category = meta.get("category", "")
    contact = meta.get("contact_type", "")
    created = meta.get("sys_created_on", "")
    return (
        f"  {rank}. id={doc_id} incident={incident} category={category} "
        f"contact_type={contact} created={created}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Query a ticket Chroma collection with smoke prompts")
    parser.add_argument(
        "persist_dir",
        type=Path,
        help="Directory containing persisted Chroma data",
    )
    parser.add_argument(
        "--collection-name",
        required=True,
        help="Name of ticket collection to query",
    )
    parser.add_argument(
        "--queries-file",
        type=Path,
        help="Optional text file with one query per line",
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=3,
        help="Number of matches to return per query",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to write machine-readable query results",
    )
    args = parser.parse_args()

    queries = _load_queries(args.queries_file)

    client = chromadb.PersistentClient(path=str(args.persist_dir))
    collection = client.get_collection(args.collection_name)

    all_results: list[dict[str, Any]] = []
    for query in queries:
        result = collection.query(query_texts=[query], n_results=args.n_results)
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        print(f"QUERY: {query}")
        rows: list[dict[str, Any]] = []
        for idx, (doc_id, metadata, distance) in enumerate(
            zip(ids, metadatas, distances),
            start=1,
        ):
            print(_format_row(idx, doc_id, metadata))
            rows.append(
                {
                    "rank": idx,
                    "doc_id": doc_id,
                    "distance": distance,
                    "metadata": metadata,
                }
            )
        all_results.append({"query": query, "results": rows})

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps({"queries": all_results}, indent=2), encoding="utf-8")
        print(f"json_out={args.json_out}")


if __name__ == "__main__":
    main()
