#!/usr/bin/env python3
"""Render a LaTeX results table from a stitched summary JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100.0:.1f}\\%"


def _fmt_score(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}"


def _escape_tex(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", required=True, help="Path to stitched summary JSON")
    parser.add_argument("--output-tex", required=True, help="Path to write LaTeX table snippet")
    parser.add_argument(
        "--include-dataset",
        action="append",
        default=[],
        help="Dataset IDs to include (can pass multiple). Defaults to all except *_failed_*",
    )
    parser.add_argument("--caption", default="Stitched CUG M2 Sonnet Results")
    parser.add_argument("--label", default="tab:cug-m2-stitched-sonnet")
    args = parser.parse_args()

    summary_path = Path(args.summary_json)
    out_path = Path(args.output_tex)

    data = json.loads(summary_path.read_text())
    datasets = data.get("datasets", [])

    include = set(args.include_dataset)
    rows = []
    for d in datasets:
        dataset_id = d.get("dataset_id", "")
        if include:
            if dataset_id not in include:
                continue
        else:
            if "_failed_" in dataset_id:
                continue
        rows.append(d)

    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\caption{" + _escape_tex(args.caption) + "}")
    lines.append("\\label{" + _escape_tex(args.label) + "}")
    lines.append("\\centering")
    lines.append("\\begin{tabular}{lrrrrr}")
    lines.append("\\toprule")
    lines.append("Dataset & Runs & Scored & Skipped & Mean Score & Pass Rate \\\\")
    lines.append("\\midrule")
    for d in rows:
        dataset_id = _escape_tex(str(d.get("dataset_id", "")))
        run_count = d.get("run_count", 0)
        scored_count = d.get("scored_count", 0)
        skipped_count = d.get("skipped_count", 0)
        score_mean = _fmt_score(d.get("score_mean"))
        pass_rate = _fmt_pct(d.get("pass_rate"))
        lines.append(
            f"{dataset_id} & {run_count} & {scored_count} & {skipped_count} & {score_mean} & {pass_rate} \\\\"
        )

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"Wrote {out_path}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
