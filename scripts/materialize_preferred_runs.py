#!/usr/bin/env python3
"""Materialize a stitched canonical experiment by preferring later sources."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--output-experiment-id", required=True)
    parser.add_argument("--output-config-id", required=True)
    parser.add_argument("--output-run-index", type=int, default=0)
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        help=(
            "Source spec: "
            "experiment_id|config_id|run_index|source_dataset_id|normalized_dataset_id|label. "
            "Provide in baseline-first order; later sources replace earlier ones."
        ),
    )
    parser.add_argument(
        "--manifest-out",
        default=None,
        help="Optional output manifest path for stitched run.json files.",
    )
    parser.add_argument(
        "--source-map-out",
        default=None,
        help="Optional output JSONL source-map path.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and recreate the output config directory if it exists.",
    )
    return parser.parse_args()


def _parse_source_spec(spec: str) -> dict[str, object]:
    parts = spec.split("|")
    if len(parts) != 6:
        raise ValueError(
            "invalid --source spec; expected "
            "experiment_id|config_id|run_index|source_dataset_id|normalized_dataset_id|label"
        )
    (
        experiment_id,
        config_id,
        run_index_raw,
        source_dataset_id,
        normalized_dataset_id,
        label,
    ) = parts
    try:
        run_index = int(run_index_raw)
    except ValueError as exc:
        raise ValueError(f"invalid run_index in source spec: {spec}") from exc
    return {
        "experiment_id": experiment_id,
        "config_id": config_id,
        "run_index": run_index,
        "source_dataset_id": source_dataset_id,
        "normalized_dataset_id": normalized_dataset_id,
        "label": label,
    }


def _load_records(
    config_dir: Path,
    run_index: int,
    source_dataset_id: str,
    normalized_dataset_id: str,
) -> dict[tuple[str, str], dict[str, object]]:
    records: dict[tuple[str, str], dict[str, object]] = {}
    for run_path in sorted(config_dir.glob(f"**/{run_index}/run.json")):
        payload = json.loads(run_path.read_text(encoding="utf-8"))
        dataset_id = payload.get("dataset_id")
        case_id = payload.get("case_id")
        if dataset_id != source_dataset_id:
            continue
        if isinstance(dataset_id, str) and isinstance(case_id, str):
            records[(normalized_dataset_id, case_id)] = {
                "run_json": run_path.resolve(),
                "source_dataset_id": dataset_id,
            }
    return records


def _rewrite_run_json(
    run_json_path: Path,
    *,
    experiment_id: str,
    output_config_id: str,
    normalized_dataset_id: str,
    output_run_index: int,
    source_run_path: str,
    source_label: str,
) -> None:
    payload = json.loads(run_json_path.read_text(encoding="utf-8"))
    payload["experiment_id"] = experiment_id
    payload["config_id"] = output_config_id
    payload["dataset_id"] = normalized_dataset_id
    payload["run_index"] = output_run_index
    payload["stitch_metadata"] = {
        "source_run_path": source_run_path,
        "source_label": source_label,
        "stitched_by": "scripts/materialize_preferred_runs.py",
    }
    run_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    parsed_sources = [_parse_source_spec(spec) for spec in args.source]

    if not parsed_sources:
        raise ValueError("at least one --source is required")

    source_records: list[dict[str, object]] = []
    for source in parsed_sources:
        config_dir = (
            Path(args.results_root).resolve()
            / str(source["experiment_id"])
            / "athos"
            / str(source["config_id"])
        )
        if not config_dir.exists():
            raise FileNotFoundError(f"source config dir not found: {config_dir}")
        records = _load_records(
            config_dir,
            int(source["run_index"]),
            str(source["source_dataset_id"]),
            str(source["normalized_dataset_id"]),
        )
        source_records.append(
            {
                **source,
                "config_dir": config_dir,
                "records": records,
            }
        )

    available_keys: set[tuple[str, str]] = set()
    for source in source_records:
        records = source["records"]
        if not isinstance(records, dict):
            continue
        available_keys.update(records.keys())
    if not available_keys:
        raise ValueError("sources produced no run records")

    output_experiment_dir = Path(args.results_root).resolve() / args.output_experiment_id
    output_config_dir = output_experiment_dir / "athos" / args.output_config_id

    if output_config_dir.exists():
        if not args.overwrite:
            raise FileExistsError(
                f"output config dir already exists: {output_config_dir} (pass --overwrite)"
            )
        shutil.rmtree(output_config_dir)
    output_config_dir.mkdir(parents=True, exist_ok=True)

    manifest_out = (
        Path(args.manifest_out).resolve()
        if args.manifest_out
        else (
            output_experiment_dir
            / "manifests"
            / f"{args.output_config_id}.manifest.txt"
        )
    )
    source_map_out = (
        Path(args.source_map_out).resolve()
        if args.source_map_out
        else (
            output_experiment_dir
            / "manifests"
            / f"{args.output_config_id}.source_map.jsonl"
        )
    )
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    source_map_out.parent.mkdir(parents=True, exist_ok=True)

    manifest_paths: list[str] = []
    source_rows: list[dict[str, object]] = []
    counts_by_dataset: Counter[str] = Counter()
    picks_by_label: Counter[str] = Counter()

    for normalized_dataset_id, case_id in sorted(available_keys):
        chosen: dict[str, object] | None = None
        for source in source_records:
            records = source["records"]
            if not isinstance(records, dict):
                continue
            candidate_key = (normalized_dataset_id, case_id)
            candidate = records.get(candidate_key)
            if candidate is None:
                continue
            chosen = {
                "run_json": candidate["run_json"],
                "label": str(source["label"]),
                "experiment_id": str(source["experiment_id"]),
                "config_id": str(source["config_id"]),
                "source_dataset_id": str(candidate["source_dataset_id"]),
                "run_index": int(source["run_index"]),
            }
        if chosen is None:
            raise RuntimeError(
                f"internal error: no chosen record for {(normalized_dataset_id, case_id)}"
            )

        source_run_json = chosen["run_json"]
        if not isinstance(source_run_json, Path):
            raise TypeError("internal error: chosen run path is not a Path")
        source_run_dir = source_run_json.parent
        dest_run_dir = (
            output_config_dir
            / normalized_dataset_id
            / case_id
            / str(args.output_run_index)
        )
        dest_run_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_run_dir, dest_run_dir)

        dest_run_json = dest_run_dir / "run.json"
        _rewrite_run_json(
            dest_run_json,
            experiment_id=args.output_experiment_id,
            output_config_id=args.output_config_id,
            normalized_dataset_id=normalized_dataset_id,
            output_run_index=args.output_run_index,
            source_run_path=str(source_run_json),
            source_label=str(chosen["label"]),
        )

        manifest_paths.append(str(dest_run_json.resolve()))
        counts_by_dataset[normalized_dataset_id] += 1
        picks_by_label[str(chosen["label"])] += 1
        source_rows.append(
            {
                "case_id": case_id,
                "normalized_dataset_id": normalized_dataset_id,
                "source_label": str(chosen["label"]),
                "source_experiment_id": str(chosen["experiment_id"]),
                "source_config_id": str(chosen["config_id"]),
                "source_dataset_id": str(chosen["source_dataset_id"]),
                "source_run_index": int(chosen["run_index"]),
                "source_run_path": str(source_run_json),
                "dest_run_path": str(dest_run_json.resolve()),
            }
        )

    manifest_out.write_text("\n".join(manifest_paths) + "\n", encoding="utf-8")
    with source_map_out.open("w", encoding="utf-8") as handle:
        for row in source_rows:
            handle.write(json.dumps(row) + "\n")

    print(f"output_experiment_id={args.output_experiment_id}")
    print(f"output_config_dir={output_config_dir}")
    print(f"manifest_out={manifest_out}")
    print(f"source_map_out={source_map_out}")
    print(f"total_runs={len(manifest_paths)}")
    print(f"counts_by_dataset={dict(sorted(counts_by_dataset.items()))}")
    print(f"picks_by_label={dict(sorted(picks_by_label.items()))}")


if __name__ == "__main__":
    main()
