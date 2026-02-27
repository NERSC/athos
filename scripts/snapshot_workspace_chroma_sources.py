#!/usr/bin/env python3
"""One-time snapshot of selected collections from a merged Chroma DB into versioned source DBs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


SCRIPT_VERSION = "1.0.0"
DEFAULT_COMPONENTS = ("docs", "consulting_docs")
DEFAULT_SOURCE_COLLECTIONS = {
    "docs": "nersc-docs",
    "consulting_docs": "nersc-consulting-docs",
}


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


def _target_db_dir(output_root: Path, logical_name: str, version: str) -> Path:
    return output_root / f"{logical_name}_db_{version}"


def _target_collection_name(logical_name: str, version: str) -> str:
    return f"{logical_name}_v1_{version}"


def _prepare_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists():
        has_content = any(path.iterdir())
        if has_content and not overwrite:
            raise FileExistsError(
                f"Target DB directory exists and is not empty: {path}. "
                "Pass --overwrite to replace it."
            )
        if overwrite:
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_collection(source_collection: Any, target_collection: Any, batch_size: int) -> int:
    copied = 0
    offset = 0
    while True:
        batch = source_collection.get(
            limit=batch_size,
            offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )
        ids = batch.get("ids") or []
        if not ids:
            break
        payload: dict[str, Any] = {"ids": ids}
        documents = batch.get("documents")
        metadatas = batch.get("metadatas")
        embeddings = batch.get("embeddings")
        if documents is not None:
            payload["documents"] = documents
        if metadatas is not None:
            payload["metadatas"] = metadatas
        if embeddings is not None:
            payload["embeddings"] = embeddings
        target_collection.upsert(**payload)
        copied += len(ids)
        offset += len(ids)
    return copied


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Snapshot selected collections from merged workspace Chroma DB into versioned source DBs"
    )
    parser.add_argument(
        "--source-persist-dir",
        type=Path,
        default=Path("/pscratch/sd/s/sfarrell/athos/workspace/chroma"),
        help="Source merged Chroma DB persist directory",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/pscratch/sd/s/sfarrell/agentic-ops/athos_chroma"),
        help="Output root for versioned source DBs",
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=None,
        help="Manifest output directory (default: <output-root>/manifests)",
    )
    parser.add_argument(
        "--version",
        default=datetime.now(timezone.utc).strftime("%Y%m%d"),
        help="Version suffix used in output DB/collection names (default: UTC YYYYMMDD)",
    )
    parser.add_argument(
        "--component",
        action="append",
        default=[],
        help="Logical component to snapshot (repeatable). Defaults to docs + consulting_docs.",
    )
    parser.add_argument(
        "--source-collection-map",
        action="append",
        default=[],
        help=(
            "Optional mapping in form logical_name=source_collection_name "
            "(repeatable). Example: --source-collection-map docs=nersc-docs"
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size used for copy operations",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing non-empty target DB dirs for selected components",
    )
    return parser.parse_args()


def _parse_source_collection_map(entries: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(
                "Invalid --source-collection-map entry. Expected logical=collection format."
            )
        logical_name, collection_name = entry.split("=", 1)
        logical_name = logical_name.strip()
        collection_name = collection_name.strip()
        if not logical_name or not collection_name:
            raise ValueError(
                "Invalid --source-collection-map entry. Expected non-empty logical=collection."
            )
        parsed[logical_name] = collection_name
    return parsed


def main() -> None:
    args = parse_args()
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be > 0")
    if not args.source_persist_dir.exists():
        raise FileNotFoundError(f"Source DB path not found: {args.source_persist_dir}")

    import chromadb

    manifest_dir = args.manifest_dir or (args.output_root / "manifests")
    components = args.component if args.component else list(DEFAULT_COMPONENTS)
    source_collection_map = dict(DEFAULT_SOURCE_COLLECTIONS)
    source_collection_map.update(_parse_source_collection_map(args.source_collection_map))
    created_utc = datetime.now(timezone.utc).isoformat()
    git_sha = _get_git_sha()

    source_client = chromadb.PersistentClient(path=str(args.source_persist_dir))
    source_collection_names = {c.name for c in source_client.list_collections()}
    for logical_name in components:
        source_collection_name = source_collection_map.get(logical_name, logical_name)
        target_db_dir = _target_db_dir(args.output_root, logical_name, args.version)
        target_collection_name = _target_collection_name(logical_name, args.version)
        manifest_path = manifest_dir / f"{logical_name}_source_snapshot_{args.version}.json"

        if source_collection_name not in source_collection_names:
            available = ", ".join(sorted(source_collection_names))
            raise ValueError(
                f"Source collection '{source_collection_name}' not found for logical component "
                f"'{logical_name}'. Available source collections: {available}"
            )
        source_collection = source_client.get_collection(source_collection_name)
        source_count = source_collection.count()
        if source_count == 0:
            raise ValueError(
                f"Source collection '{source_collection_name}' has zero documents; refusing snapshot."
            )

        _prepare_output_dir(target_db_dir, args.overwrite)
        target_client = chromadb.PersistentClient(path=str(target_db_dir))
        target_collection = target_client.get_or_create_collection(target_collection_name)
        copied_count = _copy_collection(source_collection, target_collection, args.batch_size)

        manifest = {
            "snapshot_type": "source_collection_backup",
            "logical_name": logical_name,
            "version": args.version,
            "created_utc": created_utc,
            "git_sha": git_sha,
            "script_version": SCRIPT_VERSION,
            "source_persist_dir": str(args.source_persist_dir),
            "source_collection": source_collection_name,
            "source_count": source_count,
            "target_persist_dir": str(target_db_dir),
            "target_collection": target_collection_name,
            "copied_count": copied_count,
            "status": "success",
            "errors": [],
        }
        _write_manifest(manifest_path, manifest)
        print(
            f"snapshot={logical_name} version={args.version} "
            f"target_db={target_db_dir} target_collection={target_collection_name} "
            f"copied={copied_count} manifest={manifest_path}"
        )


if __name__ == "__main__":
    main()
