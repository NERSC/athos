#!/usr/bin/env python3
"""Build a ticket_cases subset directory containing only failed cases.

The output directory contains symlinks to original case directories.
Default output path is in pscratch and named for experiment + config.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a pscratch ticket_cases subset for failed run records."
    )
    parser.add_argument(
        "--run-root",
        required=True,
        help=(
            "Root directory containing run.json files for one config, e.g. "
            "results/<experiment>/athos/<config_id>"
        ),
    )
    parser.add_argument(
        "--experiment-id",
        default="cug_m2_20260308_230032",
        help="Experiment identifier used in default output naming.",
    )
    parser.add_argument(
        "--config-id",
        default="cug_lang_chroma_sonnet__claude_sonnet__7034e2f0",
        help="Config identifier used in default output naming.",
    )
    parser.add_argument(
        "--source-ticket-cases",
        default="/pscratch/sd/s/sfarrell/athos/data/ticket_cases",
        help="Source ticket_cases directory with full case subdirectories.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Output subset directory. Default: "
            "/pscratch/sd/s/sfarrell/athos/data/ticket_cases_failed_<experiment>_<config>"
        ),
    )
    parser.add_argument(
        "--include-status",
        action="append",
        default=[],
        help=(
            "Execution status to include (repeatable). "
            "Default is all non-success statuses."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove and recreate output directory if it already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_root = Path(args.run_root).resolve()
    source_cases = Path(args.source_ticket_cases).resolve()

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        safe_exp = args.experiment_id.replace("/", "_")
        safe_cfg = args.config_id.replace("/", "_")
        output_dir = Path(
            f"/pscratch/sd/s/sfarrell/athos/data/ticket_cases_failed_{safe_exp}_{safe_cfg}"
        ).resolve()

    if not run_root.exists():
        raise FileNotFoundError(f"run root not found: {run_root}")
    if not source_cases.exists():
        raise FileNotFoundError(f"source ticket_cases not found: {source_cases}")

    include_statuses = set(args.include_status)
    failed_case_ids: set[str] = set()
    scanned = 0

    for run_path in sorted(run_root.glob("**/run.json")):
        scanned += 1
        payload = json.loads(run_path.read_text())
        if payload.get("dataset_id") != "ticket_cases":
            continue
        status = (
            payload.get("execution", {}).get("status")
            if isinstance(payload.get("execution"), dict)
            else None
        )
        if include_statuses:
            if status not in include_statuses:
                continue
        else:
            if status == "success":
                continue
        case_id = payload.get("case_id")
        if isinstance(case_id, str) and case_id:
            failed_case_ids.add(case_id)

    if output_dir.exists():
        if not args.overwrite:
            raise FileExistsError(
                f"output dir exists: {output_dir} (pass --overwrite to recreate)"
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    linked = 0
    missing = []
    for case_id in sorted(failed_case_ids):
        src = source_cases / case_id
        dst = output_dir / case_id
        if not src.is_dir():
            missing.append(case_id)
            continue
        dst.symlink_to(src)
        linked += 1

    print(f"scanned_run_json={scanned}")
    print(f"failed_ticket_cases={len(failed_case_ids)}")
    print(f"linked_cases={linked}")
    print(f"missing_source_cases={len(missing)}")
    print(f"output_dir={output_dir}")
    if missing:
        print("missing_case_ids:")
        for case_id in missing:
            print(f"  {case_id}")


if __name__ == "__main__":
    main()
