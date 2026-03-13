#!/usr/bin/env python3
"""Plot per-case score variance for one repeated-run CUG config."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--judgments-jsonl",
        required=True,
        help="Path to a judgments JSONL file for one config/run set.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output image path, e.g. results/cug_m3_variance_by_case.png",
    )
    parser.add_argument(
        "--title",
        default="Per-Case Score Variance Across Repeated Runs",
        help="Figure title.",
    )
    parser.add_argument(
        "--dataset-order",
        action="append",
        default=["simple_qa", "test_cases"],
        help="Dataset display order. Repeatable.",
    )
    parser.add_argument(
        "--show-failure-counts",
        action="store_true",
        help="Annotate x-axis labels with count of zero-score attempts.",
    )
    parser.add_argument(
        "--figsize",
        default="12,8",
        help="Figure size in inches as width,height.",
    )
    return parser.parse_args()


def _load_judgments(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _extract_run_parts(run_path: str) -> tuple[str, str, str] | None:
    parts = Path(run_path).parts
    if len(parts) < 6:
        return None
    # .../<config_id>/<dataset_id>/<case_id>/<run_index>/run.json
    return parts[-5], parts[-4], parts[-3]


def _short_panel_title(config_id: str) -> str:
    if "sonnet" in config_id:
        model = "Claude Sonnet"
    elif "gptoss" in config_id:
        model = "GPT-OSS"
    else:
        model = config_id
    harness = "LangChain" if "cug_lang_" in config_id else "Other"
    return f"{harness} / {model}"


def _build_case_order(
    rows: list[dict[str, Any]],
    dataset_order: list[str],
) -> list[tuple[str, str]]:
    seen: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        run_path = row.get("run_path")
        if not isinstance(run_path, str) or not run_path:
            continue
        parsed = _extract_run_parts(run_path)
        if parsed is None:
            continue
        _, dataset_id, case_id = parsed
        if case_id not in seen[dataset_id]:
            seen[dataset_id].append(case_id)

    ordered: list[tuple[str, str]] = []
    for dataset_id in dataset_order:
        for case_id in sorted(seen.get(dataset_id, [])):
            ordered.append((dataset_id, case_id))
    for dataset_id in sorted(seen):
        if dataset_id in dataset_order:
            continue
        for case_id in sorted(seen[dataset_id]):
            ordered.append((dataset_id, case_id))
    return ordered


def _load_panel(
    judgment_path: Path,
    dataset_order: list[str],
) -> dict[str, Any]:
    rows = _load_judgments(judgment_path)
    by_case: dict[tuple[str, str], list[float]] = defaultdict(list)
    config_ids: set[str] = set()
    for row in rows:
        run_path = row.get("run_path")
        score = row.get("score")
        if not isinstance(run_path, str) or not run_path:
            continue
        if not isinstance(score, (int, float)):
            continue
        parsed = _extract_run_parts(run_path)
        if parsed is None:
            continue
        config_id, dataset_id, case_id = parsed
        config_ids.add(config_id)
        by_case[(dataset_id, case_id)].append(float(score))

    if not by_case:
        raise ValueError(f"No usable scored judgments found in {judgment_path}")
    if len(config_ids) != 1:
        raise ValueError(
            f"Expected one config_id in {judgment_path}, found {sorted(config_ids)}"
        )
    config_id = next(iter(config_ids))
    case_order = _build_case_order(rows, dataset_order)
    return {
        "path": judgment_path,
        "config_id": config_id,
        "title": _short_panel_title(config_id),
        "case_order": case_order,
        "scores": by_case,
    }


def main() -> None:
    args = parse_args()
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for plot_cug_variance_by_case.py"
        ) from exc

    panel = _load_panel(Path(args.judgments_jsonl), args.dataset_order)
    try:
        fig_width, fig_height = [float(x.strip()) for x in args.figsize.split(",", 1)]
    except Exception as exc:
        raise SystemExit("--figsize must be width,height, e.g. 12,8") from exc

    fig, ax = plt.subplots(
        1,
        1,
        figsize=(fig_width, fig_height),
        squeeze=True,
    )

    panel_facecolors = {
        "simple_qa": "#f4f1e8",
        "test_cases": "#e8eef6",
    }
    box_facecolors = {
        "simple_qa": "#c98f2d",
        "test_cases": "#3d6ea8",
    }
    point_facecolors = {
        "simple_qa": "#8a5b12",
        "test_cases": "#1f4d7a",
    }

    case_order = panel["case_order"]
    positions = list(range(1, len(case_order) + 1))
    data = [panel["scores"].get(key, []) for key in case_order]
    labels = [case_id for _, case_id in case_order]

        # Add subtle dataset shading bands behind the boxes.
    current_start = 1
    current_dataset = case_order[0][0] if case_order else None
    for idx, (dataset_id, _) in enumerate(case_order, start=1):
        if dataset_id != current_dataset:
            ax.axvspan(
                current_start - 0.5,
                idx - 0.5,
                color=panel_facecolors.get(current_dataset, "#f2f2f2"),
                alpha=0.20,
                zorder=0,
            )
            current_start = idx
            current_dataset = dataset_id
    if current_dataset is not None:
        ax.axvspan(
            current_start - 0.5,
            len(case_order) + 0.5,
            color=panel_facecolors.get(current_dataset, "#f2f2f2"),
            alpha=0.20,
            zorder=0,
        )

    bp = ax.boxplot(
        data,
        positions=positions,
        widths=0.6,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "#111111", "linewidth": 1.6},
        whiskerprops={"color": "#444444", "linewidth": 1.2},
        capprops={"color": "#444444", "linewidth": 1.2},
        boxprops={"linewidth": 1.2, "edgecolor": "#333333"},
    )

    for patch, (dataset_id, _) in zip(bp["boxes"], case_order):
        patch.set_facecolor(box_facecolors.get(dataset_id, "#bbbbbb"))
        patch.set_alpha(0.65)

        # Overlay raw points with deterministic horizontal offsets.
    for pos, key in zip(positions, case_order):
        values = panel["scores"].get(key, [])
        if not values:
            continue
        offsets = []
        if len(values) == 1:
            offsets = [0.0]
        else:
            span = 0.18
            offsets = [
                (-span + (2 * span * i / (len(values) - 1))) for i in range(len(values))
            ]
        dataset_id, _ = key
        ax.scatter(
            [pos + off for off in offsets],
            values,
            s=26,
            color=point_facecolors.get(dataset_id, "#333333"),
            alpha=0.85,
            linewidths=0,
            zorder=3,
        )

    if args.show_failure_counts:
        labels = []
        for key in case_order:
            values = panel["scores"].get(key, [])
            zero_count = sum(1 for v in values if v == 0.0)
            suffix = f"\n(zeros:{zero_count})" if zero_count else ""
            labels.append(f"{key[1]}{suffix}")

        # Mark the boundary between QA and test cases.
    for idx in range(1, len(case_order)):
        if case_order[idx - 1][0] != case_order[idx][0]:
            ax.axvline(idx + 0.5, color="#666666", linestyle="--", linewidth=1.0)

    ax.set_ylabel("Score", fontsize=18)
    ax.set_ylim(-2, 102)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=14)
    ax.tick_params(axis="y", labelsize=14)
    ax.grid(axis="y", alpha=0.25, linestyle=":", linewidth=0.8)

    fig.suptitle(args.title, fontsize=22, fontweight="bold", y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
