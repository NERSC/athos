#!/usr/bin/env python3
"""Build a ticket_cases subset directory from an explicit case-id list."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case-list",
        required=True,
        help="Text file containing one case_id per line.",
    )
    parser.add_argument(
        "--source-ticket-cases",
        default="/pscratch/sd/s/sfarrell/athos/data/ticket_cases",
        help="Source ticket_cases directory with full case subdirectories.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Destination subset directory to create.",
    )
    parser.add_argument(
        "--mode",
        choices=("symlink", "copy"),
        default="symlink",
        help="How to materialize each selected case directory.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove and recreate output-dir if it already exists.",
    )
    return parser.parse_args()


def _load_case_ids(path: Path) -> list[str]:
    case_ids: list[str] = []
    seen: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line in seen:
            continue
        seen.add(line)
        case_ids.append(line)
    return case_ids


def main() -> None:
    args = parse_args()

    case_list_path = Path(args.case_list).resolve()
    source_cases = Path(args.source_ticket_cases).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not case_list_path.is_file():
        raise FileNotFoundError(f"case list not found: {case_list_path}")
    if not source_cases.is_dir():
        raise FileNotFoundError(f"source ticket_cases not found: {source_cases}")

    case_ids = _load_case_ids(case_list_path)
    if not case_ids:
        raise ValueError(f"no case IDs found in {case_list_path}")

    if output_dir.exists():
        if not args.overwrite:
            raise FileExistsError(
                f"output dir exists: {output_dir} (pass --overwrite to recreate)"
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    materialized = 0
    missing: list[str] = []
    for case_id in case_ids:
        src = source_cases / case_id
        dst = output_dir / case_id
        if not src.is_dir():
            missing.append(case_id)
            continue
        if args.mode == "symlink":
            dst.symlink_to(src)
        else:
            shutil.copytree(src, dst)
        materialized += 1

    print(f"case_ids_requested={len(case_ids)}")
    print(f"materialized_cases={materialized}")
    print(f"missing_source_cases={len(missing)}")
    print(f"mode={args.mode}")
    print(f"output_dir={output_dir}")
    if missing:
        print("missing_case_ids:")
        for case_id in missing:
            print(f"  {case_id}")


if __name__ == "__main__":
    main()
