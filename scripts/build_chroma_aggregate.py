#!/usr/bin/env python3
"""Build curated aggregate ChromaDB artifacts from a YAML spec."""

from __future__ import annotations

import argparse
from pathlib import Path

from athos.utils.chroma_aggregate import build_aggregate, load_aggregate_spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a curated aggregate ChromaDB from source DBs")
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path("config/chroma_aggregate_spec.yaml"),
        help="Path to aggregate build spec YAML",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = load_aggregate_spec(args.spec)
    manifest = build_aggregate(spec)
    print(
        "Aggregate build complete: "
        f"{manifest['aggregate_name']}@{manifest['aggregate_version']} "
        f"total_copied_count={manifest['total_copied_count']} status={manifest['status']}"
    )
    print(f"Manifest written to: {spec.output.manifest_out}")


if __name__ == "__main__":
    main()
