#!/usr/bin/env python3
"""Build a runs-manifest that prefers new rerun records when present.

For each baseline case in old config (run_index=0):
- use new config run_index=1 if it exists
- otherwise fall back to old config run_index=0

This is useful for stitching partial reruns into a single scoreable manifest.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a stitched manifest: prefer new run if it exists, else old run."
    )
    parser.add_argument(
        "--experiment-id",
        default="cug_m2_20260308_230032",
        help="Experiment directory under results/.",
    )
    parser.add_argument(
        "--results-root",
        default="results",
        help="Root containing experiment outputs.",
    )
    parser.add_argument(
        "--old-config-id",
        default="cug_lang_chroma_sonnet__claude_sonnet__7034e2f0",
        help="Baseline config_id to use as case universe (run_index=0).",
    )
    parser.add_argument(
        "--new-config-id",
        default="cug_lang_chroma_sonnet__claude_sonnet__19c4421d",
        help="Rerun config_id to prefer when run_index=1 exists.",
    )
    parser.add_argument(
        "--new-ticket-dataset-id",
        default=(
            "ticket_cases_failed_cug_m2_20260308_230032_"
            "cug_lang_chroma_sonnet__claude_sonnet__7034e2f0"
        ),
        help=(
            "Dataset id used by rerun ticket subset. "
            "Mapped back to baseline ticket_cases by case_id."
        ),
    )
    parser.add_argument(
        "--old-run-index",
        type=int,
        default=0,
        help="Baseline run_index to fall back to.",
    )
    parser.add_argument(
        "--new-run-index",
        type=int,
        default=1,
        help="Rerun run_index to prefer.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Output manifest path. Default: "
            "results/<experiment-id>/manifests/sonnet_prefer_new_if_exists.manifest.txt"
        ),
    )
    return parser.parse_args()


def _load_run_records(config_dir: Path, run_index: int) -> dict[tuple[str, str, int], Path]:
    records: dict[tuple[str, str, int], Path] = {}
    pattern = f"**/{run_index}/run.json"
    for run_path in sorted(config_dir.glob(pattern)):
        payload = json.loads(run_path.read_text())
        key = (
            str(payload.get("dataset_id")),
            str(payload.get("case_id")),
            int(payload.get("run_index", run_index)),
        )
        records[key] = run_path.resolve()
    return records


def main() -> None:
    args = parse_args()

    exp_dir = Path(args.results_root).resolve() / args.experiment_id / "athos"
    old_dir = exp_dir / args.old_config_id
    new_dir = exp_dir / args.new_config_id

    if not old_dir.exists():
        raise FileNotFoundError(f"old config directory not found: {old_dir}")
    if not new_dir.exists():
        raise FileNotFoundError(f"new config directory not found: {new_dir}")

    old_records = _load_run_records(old_dir, args.old_run_index)
    new_records = _load_run_records(new_dir, args.new_run_index)

    if not old_records:
        raise ValueError(
            f"No old run records found under {old_dir} for run_index={args.old_run_index}"
        )

    manifest_paths: list[Path] = []
    picked_new = 0
    picked_old = 0

    # Use baseline old config as the target case universe.
    for (dataset_id, case_id, _), old_path in sorted(old_records.items()):
        if dataset_id == "ticket_cases":
            new_key = (args.new_ticket_dataset_id, case_id, args.new_run_index)
        else:
            new_key = (dataset_id, case_id, args.new_run_index)

        new_path = new_records.get(new_key)
        if new_path is not None:
            manifest_paths.append(new_path)
            picked_new += 1
        else:
            manifest_paths.append(old_path)
            picked_old += 1

    output = (
        Path(args.output).resolve()
        if args.output
        else (
            Path(args.results_root).resolve()
            / args.experiment_id
            / "manifests"
            / "sonnet_prefer_new_if_exists.manifest.txt"
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(str(p) for p in manifest_paths) + "\n")

    print(f"wrote_manifest={output}")
    print(f"total_paths={len(manifest_paths)}")
    print(f"picked_new={picked_new}")
    print(f"picked_old_fallback={picked_old}")


if __name__ == "__main__":
    main()
