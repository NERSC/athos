#!/usr/bin/env python3
"""Materialize a canonical stitched Sonnet-Chroma runset.

Builds a new config directory under results/<experiment>/athos/<output-config-id>
by choosing runs from:
- old config run_index=old-run-index (baseline universe)
- new config run_index=new-run-index when present

Ticket rerun dataset IDs are normalized back to `ticket_cases` so downstream
scoring and summarization treat the stitched output as a regular canonical runset.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-id", default="cug_m2_20260308_230032")
    parser.add_argument("--results-root", default="results")
    parser.add_argument(
        "--output-experiment-id",
        default=None,
        help=(
            "Destination experiment id for stitched outputs. "
            "Default: <experiment-id>_stitched_sonnet"
        ),
    )
    parser.add_argument(
        "--old-config-id",
        default="cug_lang_chroma_sonnet__claude_sonnet__7034e2f0",
    )
    parser.add_argument(
        "--new-config-id",
        default="cug_lang_chroma_sonnet__claude_sonnet__19c4421d",
    )
    parser.add_argument(
        "--output-config-id",
        default="cug_lang_chroma_sonnet__claude_sonnet__stitched_19c4421d_over_7034e2f0",
    )
    parser.add_argument("--old-run-index", type=int, default=0)
    parser.add_argument("--new-run-index", type=int, default=1)
    parser.add_argument("--output-run-index", type=int, default=0)
    parser.add_argument("--old-ticket-dataset-id", default="ticket_cases")
    parser.add_argument(
        "--new-ticket-dataset-id",
        default=(
            "ticket_cases_failed_cug_m2_20260308_230032_"
            "cug_lang_chroma_sonnet__claude_sonnet__7034e2f0"
        ),
    )
    parser.add_argument(
        "--manifest-out",
        default=None,
        help="Output manifest path for stitched run.json paths (default under results/.../manifests).",
    )
    parser.add_argument(
        "--source-map-out",
        default=None,
        help="Output JSONL source-map path (default under results/.../manifests).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and recreate output config directory if it exists.",
    )
    return parser.parse_args()


def _load_records(config_dir: Path, run_index: int) -> dict[tuple[str, str], Path]:
    records: dict[tuple[str, str], Path] = {}
    for run_path in sorted(config_dir.glob(f"**/{run_index}/run.json")):
        payload = json.loads(run_path.read_text())
        dataset_id = payload.get("dataset_id")
        case_id = payload.get("case_id")
        if not (isinstance(dataset_id, str) and isinstance(case_id, str)):
            continue
        records[(dataset_id, case_id)] = run_path.resolve()
    return records


def _rewrite_run_json(
    run_json_path: Path,
    *,
    experiment_id: str,
    output_config_id: str,
    normalized_dataset_id: str,
    output_run_index: int,
    source_run_path: str,
) -> None:
    payload = json.loads(run_json_path.read_text())
    payload["experiment_id"] = experiment_id
    payload["config_id"] = output_config_id
    payload["dataset_id"] = normalized_dataset_id
    payload["run_index"] = output_run_index
    payload["stitch_metadata"] = {
        "source_run_path": source_run_path,
        "stitched_by": "scripts/materialize_stitched_sonnet_runs.py",
    }
    run_json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> None:
    args = parse_args()

    input_exp_root = Path(args.results_root).resolve() / args.experiment_id
    input_athos_root = input_exp_root / "athos"
    old_config_dir = input_athos_root / args.old_config_id
    new_config_dir = input_athos_root / args.new_config_id

    output_experiment_id = (
        args.output_experiment_id
        if args.output_experiment_id
        else f"{args.experiment_id}_stitched_sonnet"
    )
    output_exp_root = Path(args.results_root).resolve() / output_experiment_id
    output_athos_root = output_exp_root / "athos"
    out_config_dir = output_athos_root / args.output_config_id

    if not old_config_dir.exists():
        raise FileNotFoundError(f"old config dir not found: {old_config_dir}")
    if not new_config_dir.exists():
        raise FileNotFoundError(f"new config dir not found: {new_config_dir}")

    if out_config_dir.exists():
        if not args.overwrite:
            raise FileExistsError(
                f"output config dir already exists: {out_config_dir} (pass --overwrite)"
            )
        shutil.rmtree(out_config_dir)
    out_config_dir.mkdir(parents=True, exist_ok=True)

    old_records = _load_records(old_config_dir, args.old_run_index)
    new_records = _load_records(new_config_dir, args.new_run_index)
    if not old_records:
        raise ValueError(
            f"no baseline runs found in {old_config_dir} (run_index={args.old_run_index})"
        )

    manifest_out = (
        Path(args.manifest_out).resolve()
        if args.manifest_out
        else (
            output_exp_root
            / "manifests"
            / f"{args.output_config_id}.manifest.txt"
        )
    )
    source_map_out = (
        Path(args.source_map_out).resolve()
        if args.source_map_out
        else (
            output_exp_root
            / "manifests"
            / f"{args.output_config_id}.source_map.jsonl"
        )
    )
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    source_map_out.parent.mkdir(parents=True, exist_ok=True)

    chosen_new = 0
    chosen_old = 0
    counts_by_dataset: Counter[str] = Counter()
    manifest_paths: list[str] = []
    source_rows: list[dict] = []

    for (old_dataset_id, case_id), old_run_json in sorted(old_records.items()):
        normalized_dataset_id = old_dataset_id
        if old_dataset_id == args.old_ticket_dataset_id:
            candidate_new_key = (args.new_ticket_dataset_id, case_id)
        else:
            candidate_new_key = (old_dataset_id, case_id)

        chosen_run_json = new_records.get(candidate_new_key)
        source_config_id = args.new_config_id
        source_dataset_id = candidate_new_key[0]
        source_run_index = args.new_run_index
        source_pick = "new"
        if chosen_run_json is None:
            chosen_run_json = old_run_json
            source_config_id = args.old_config_id
            source_dataset_id = old_dataset_id
            source_run_index = args.old_run_index
            source_pick = "old"

        if source_pick == "new":
            chosen_new += 1
        else:
            chosen_old += 1

        source_run_dir = chosen_run_json.parent
        dest_run_dir = out_config_dir / normalized_dataset_id / case_id / str(args.output_run_index)
        dest_run_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_run_dir, dest_run_dir)

        dest_run_json = dest_run_dir / "run.json"
        _rewrite_run_json(
            dest_run_json,
            experiment_id=output_experiment_id,
            output_config_id=args.output_config_id,
            normalized_dataset_id=normalized_dataset_id,
            output_run_index=args.output_run_index,
            source_run_path=str(chosen_run_json),
        )

        manifest_paths.append(str(dest_run_json.resolve()))
        counts_by_dataset[normalized_dataset_id] += 1
        source_rows.append(
            {
                "case_id": case_id,
                "normalized_dataset_id": normalized_dataset_id,
                "source_pick": source_pick,
                "source_config_id": source_config_id,
                "source_dataset_id": source_dataset_id,
                "source_run_index": source_run_index,
                "source_run_path": str(chosen_run_json),
                "dest_run_path": str(dest_run_json.resolve()),
            }
        )

    manifest_out.write_text("\n".join(manifest_paths) + "\n")
    with source_map_out.open("w", encoding="utf-8") as handle:
        for row in source_rows:
            handle.write(json.dumps(row) + "\n")

    print(f"input_experiment_id={args.experiment_id}")
    print(f"output_experiment_id={output_experiment_id}")
    print(f"output_config_dir={out_config_dir}")
    print(f"manifest_out={manifest_out}")
    print(f"source_map_out={source_map_out}")
    print(f"total_runs={len(manifest_paths)}")
    print(f"picked_new={chosen_new}")
    print(f"picked_old={chosen_old}")
    print(f"counts_by_dataset={dict(sorted(counts_by_dataset.items()))}")


if __name__ == "__main__":
    main()
