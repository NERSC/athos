#!/usr/bin/env python3
"""Materialize a canonical CUG M2 experiment from selected config result dirs.

This creates a new results experiment directory with:
- athos/<config_id> entries (symlinks by default, optional copies)
- manifests/canonical_manifest.json (provenance + counts)
- manifests/all_runs.manifest.txt (absolute run.json paths)
- judgments/*.jsonl (selected judgment files materialized at experiment level)
- manifests/judgments_manifest.json (judgment provenance)

The default mapping matches the configs currently used in the paper table.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DEFAULT_OUTPUT_EXPERIMENT_ID = "cug_m2_20260308_230032_canonical_table_v1"

DEFAULT_CONFIG_SOURCES = [
    (
        "cug_lang_base_gptoss__gptoss__6dc3cc9e",
        "results/cug_m2_20260308_230032/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e",
    ),
    (
        "cug_lang_chroma_gptoss__gptoss__b046b443",
        "results/cug_m2_20260308_230032/athos/cug_lang_chroma_gptoss__gptoss__b046b443",
    ),
    (
        "cug_lang_base_sonnet__claude_sonnet__007abbd4",
        "results/cug_m2_20260308_230032/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4",
    ),
    (
        "cug_lang_chroma_sonnet__claude_sonnet__stitched_19c4421d_over_7034e2f0",
        (
            "results/cug_m2_20260308_230032_stitched_sonnet/athos/"
            "cug_lang_chroma_sonnet__claude_sonnet__stitched_19c4421d_over_7034e2f0"
        ),
    ),
]

DEFAULT_JUDGMENT_SOURCES = [
    (
        "gptoss_rubric_v1_cug_lang_base_gptoss__gptoss__6dc3cc9e.jsonl",
        "results/cug_m2_20260308_230032/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/judgments/gptoss_rubric_v1_cug_lang_base_gptoss__gptoss__6dc3cc9e.jsonl",
    ),
    (
        "gptoss_rubric_v1_cug_lang_base_gptoss__gptoss__6dc3cc9e.skips.jsonl",
        "results/cug_m2_20260308_230032/athos/cug_lang_base_gptoss__gptoss__6dc3cc9e/judgments/gptoss_rubric_v1_cug_lang_base_gptoss__gptoss__6dc3cc9e.skips.jsonl",
    ),
    (
        "gptoss_rubric_v1_cug_lang_chroma_gptoss__gptoss__b046b443.jsonl",
        "results/cug_m2_20260308_230032/athos/cug_lang_chroma_gptoss__gptoss__b046b443/judgments/gptoss_rubric_v1_cug_lang_chroma_gptoss__gptoss__b046b443.jsonl",
    ),
    (
        "gptoss_rubric_v1_cug_lang_chroma_gptoss__gptoss__b046b443.skips.jsonl",
        "results/cug_m2_20260308_230032/athos/cug_lang_chroma_gptoss__gptoss__b046b443/judgments/gptoss_rubric_v1_cug_lang_chroma_gptoss__gptoss__b046b443.skips.jsonl",
    ),
    (
        "gptoss_rubric_v1_cug_lang_base_sonnet__claude_sonnet__007abbd4.jsonl",
        "results/cug_m2_20260308_230032/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/judgments/gptoss_rubric_v1_cug_lang_base_sonnet__claude_sonnet__007abbd4.jsonl",
    ),
    (
        "gptoss_rubric_v1_cug_lang_base_sonnet__claude_sonnet__007abbd4.skips.jsonl",
        "results/cug_m2_20260308_230032/athos/cug_lang_base_sonnet__claude_sonnet__007abbd4/judgments/gptoss_rubric_v1_cug_lang_base_sonnet__claude_sonnet__007abbd4.skips.jsonl",
    ),
    (
        "gptoss_rubric_v1_sonnet_stitched_canonical.jsonl",
        "results/cug_m2_20260308_230032_stitched_sonnet/judgments/gptoss_rubric_v1_sonnet_stitched_canonical.jsonl",
    ),
    (
        "gptoss_rubric_v1_sonnet_stitched_canonical.skips.jsonl",
        "results/cug_m2_20260308_230032_stitched_sonnet/judgments/gptoss_rubric_v1_sonnet_stitched_canonical.skips.jsonl",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--output-experiment-id", default=DEFAULT_OUTPUT_EXPERIMENT_ID)
    parser.add_argument(
        "--mode",
        choices=["symlink", "copy"],
        default="symlink",
        help="How to materialize config dirs into canonical experiment.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete output experiment directory if it already exists.",
    )
    parser.add_argument(
        "--include-skips",
        action="store_true",
        help="Also include *.skips.jsonl files in canonical experiment-level judgments.",
    )
    return parser.parse_args()


def _count_runs(config_dir: Path) -> int:
    return len(list(config_dir.glob("**/run.json")))


def _collect_run_paths(config_dir: Path) -> list[str]:
    return sorted(str(p.resolve()) for p in config_dir.glob("**/run.json"))


def main() -> None:
    args = parse_args()

    results_root = Path(args.results_root).resolve()
    output_root = results_root / args.output_experiment_id
    output_athos = output_root / "athos"
    output_judgments = output_root / "judgments"
    output_manifests = output_root / "manifests"

    if output_root.exists():
        if not args.overwrite:
            raise FileExistsError(f"Output experiment already exists: {output_root} (pass --overwrite)")
        shutil.rmtree(output_root)

    output_athos.mkdir(parents=True, exist_ok=True)
    output_judgments.mkdir(parents=True, exist_ok=True)
    output_manifests.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    judgment_rows = []
    all_runs: list[str] = []

    for config_id, source in DEFAULT_CONFIG_SOURCES:
        source_path = Path(source).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source config directory not found: {source_path}")

        dest_path = output_athos / config_id
        if args.mode == "symlink":
            dest_path.symlink_to(source_path, target_is_directory=True)
        else:
            shutil.copytree(source_path, dest_path)

        run_count = _count_runs(source_path)
        run_paths = _collect_run_paths(source_path)
        all_runs.extend(run_paths)

        manifest_rows.append(
            {
                "config_id": config_id,
                "source_config_dir": str(source_path),
                "materialized_path": str(dest_path.resolve()),
                "mode": args.mode,
                "run_count": run_count,
            }
        )

    for output_name, source in DEFAULT_JUDGMENT_SOURCES:
        if not args.include_skips and output_name.endswith(".skips.jsonl"):
            continue
        source_path = Path(source).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Judgment source file not found: {source_path}")
        dest_path = output_judgments / output_name
        if args.mode == "symlink":
            dest_path.symlink_to(source_path)
        else:
            shutil.copy2(source_path, dest_path)
        judgment_rows.append(
            {
                "judgment_file": output_name,
                "source_path": str(source_path),
                "materialized_path": str(dest_path.resolve()),
                "mode": args.mode,
            }
        )

    all_runs = sorted(set(all_runs))
    (output_manifests / "all_runs.manifest.txt").write_text("\n".join(all_runs) + "\n")

    canonical_manifest = {
        "schema_version": "athos.canonical_manifest.v1",
        "output_experiment_id": args.output_experiment_id,
        "output_root": str(output_root),
        "mode": args.mode,
        "configs": manifest_rows,
        "total_configs": len(manifest_rows),
        "total_runs": len(all_runs),
    }
    (output_manifests / "canonical_manifest.json").write_text(
        json.dumps(canonical_manifest, indent=2, sort_keys=True) + "\n"
    )
    (output_manifests / "judgments_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "athos.judgments_manifest.v1",
                "output_experiment_id": args.output_experiment_id,
                "mode": args.mode,
                "include_skips": bool(args.include_skips),
                "judgments": judgment_rows,
                "total_judgment_files": len(judgment_rows),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    print(f"output_experiment={output_root}")
    print(f"mode={args.mode}")
    print(f"total_configs={len(manifest_rows)}")
    print(f"total_runs={len(all_runs)}")
    print(f"total_judgment_files={len(judgment_rows)}")
    print(f"manifest_json={output_manifests / 'canonical_manifest.json'}")
    print(f"manifest_runs={output_manifests / 'all_runs.manifest.txt'}")
    print(f"manifest_judgments={output_manifests / 'judgments_manifest.json'}")


if __name__ == "__main__":
    main()
