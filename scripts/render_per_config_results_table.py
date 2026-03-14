#!/usr/bin/env python3
"""Render a wide per-config LaTeX table by merging multiple summary JSON files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _escape_tex(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
    )


def _fmt_score(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.1f}"
    return "N/A"


def _fmt_pct(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100.0:.1f}\\%"
    return "N/A"


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary-json",
        action="append",
        required=True,
        help="Summary JSON path from evals/summarize_results.py (repeatable).",
    )
    parser.add_argument("--output-tex", required=True)
    parser.add_argument(
        "--include-dataset",
        action="append",
        default=[],
        help="Only include these dataset IDs (repeatable). Default includes all datasets.",
    )
    parser.add_argument(
        "--include-config-substring",
        action="append",
        default=[],
        help="Only include configs whose config_id contains any provided substring.",
    )
    parser.add_argument(
        "--exclude-zero-scored",
        action="store_true",
        help="Drop rows with scored_count == 0.",
    )
    parser.add_argument(
        "--caption",
        default=(
            "Per-Configuration Results on NERSC QA and Ticket Datasets "
            "(Tokens I/O/T = mean input/output/total tokens per run; "
            "Lat = median end-to-end latency)"
        ),
    )
    parser.add_argument(
        "--label",
        default="tab:cug-results-per-config",
    )
    parser.add_argument(
        "--dataset-order",
        action="append",
        default=["nersc_qa.v2", "ticket_cases"],
        help="Dataset column order for wide table (repeatable).",
    )
    return parser.parse_args()


def _include_row(
    row: dict[str, Any],
    include_dataset: set[str],
    include_config_substrings: list[str],
    exclude_zero_scored: bool,
) -> bool:
    dataset_id = str(row.get("dataset_id", ""))
    config_id = str(row.get("config_id", ""))
    scored_count = row.get("scored_count")

    if include_dataset and dataset_id not in include_dataset:
        return False

    if include_config_substrings and not any(s in config_id for s in include_config_substrings):
        return False

    if exclude_zero_scored and not (isinstance(scored_count, int) and scored_count > 0):
        return False

    return True


def _pick_better(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    # Prefer row with more scored runs; tie-break on newer summary timestamp.
    ex_scored = existing.get("scored_count")
    ca_scored = candidate.get("scored_count")
    if isinstance(ca_scored, int) and isinstance(ex_scored, int):
        if ca_scored > ex_scored:
            return candidate
        if ex_scored > ca_scored:
            return existing
    ex_ts = _parse_ts(existing.get("_summary_generated_at_utc"))
    ca_ts = _parse_ts(candidate.get("_summary_generated_at_utc"))
    if ex_ts is None and ca_ts is None:
        return candidate
    if ex_ts is None:
        return candidate
    if ca_ts is None:
        return existing
    return candidate if ca_ts >= ex_ts else existing


def _short_config_id(config_id: str) -> str:
    harness = "lang" if "_lang_" in config_id or config_id.startswith("cug_lang_") else "unknown"
    if "sonnet" in config_id:
        model = "sonnet"
    elif "gptoss" in config_id:
        model = "gptoss"
    else:
        model = "unknown"
    if "filesystem" in config_id:
        tools = "filesystem"
    elif "chroma" in config_id and "opt" in config_id:
        tools = "chroma_opt"
    elif "chroma" in config_id:
        tools = "chroma"
    elif "base" in config_id:
        tools = "base"
    else:
        tools = "unknown"
    return f"{harness}_{model}_{tools}"


def _fmt_pass_score(pass_rate: Any, score_mean: Any) -> str:
    return f"{_fmt_pct(pass_rate)} / {_fmt_score(score_mean)}"


def _fmt_fail_count(skipped_count: Any) -> str:
    if isinstance(skipped_count, int):
        return str(skipped_count)
    return "N/A"


def _fmt_tokens_k(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) / 1000.0:.1f}k"
    return "N/A"


def _fmt_latency_s(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) / 1000.0:.1f}s"
    return "N/A"


def _fmt_tokens_iot(ds: dict[str, Any]) -> str:
    tok_in = _fmt_tokens_k(ds.get("tokens_input_mean"))
    tok_out = _fmt_tokens_k(ds.get("tokens_output_mean"))
    tok_tot = _fmt_tokens_k(ds.get("tokens_total_mean"))
    return f"{tok_in}/{tok_out}/{tok_tot}"


def main() -> None:
    args = parse_args()
    include_dataset = set(args.include_dataset)
    include_config_substrings = args.include_config_substring

    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    loaded_summaries = 0
    skipped_non_aggregate = 0

    for summary_path_str in args.summary_json:
        summary_path = Path(summary_path_str)
        payload = json.loads(summary_path.read_text())
        aggregates = payload.get("aggregates")
        if not isinstance(aggregates, list):
            skipped_non_aggregate += 1
            continue
        loaded_summaries += 1
        generated_at = payload.get("generated_at_utc")
        for row in aggregates:
            if not isinstance(row, dict):
                continue
            row = dict(row)
            row["_summary_path"] = str(summary_path.resolve())
            row["_summary_generated_at_utc"] = generated_at
            if not _include_row(row, include_dataset, include_config_substrings, args.exclude_zero_scored):
                continue
            key = (str(row.get("config_id", "")), str(row.get("dataset_id", "")))
            existing = rows_by_key.get(key)
            if existing is None:
                rows_by_key[key] = row
            else:
                rows_by_key[key] = _pick_better(existing, row)

    rows = sorted(
        rows_by_key.values(),
        key=lambda r: (str(r.get("config_id", "")), str(r.get("dataset_id", ""))),
    )

    dataset_order = args.dataset_order
    if include_dataset:
        dataset_order = [d for d in dataset_order if d in include_dataset]
    if not dataset_order:
        dataset_order = sorted({str(r.get("dataset_id", "")) for r in rows})

    by_config: dict[str, dict[str, Any]] = {}
    for row in rows:
        config_id = str(row.get("config_id", ""))
        dataset_id = str(row.get("dataset_id", ""))
        cfg_bucket = by_config.setdefault(
            config_id,
            {
                "config_id": config_id,
                "short_config_id": _short_config_id(config_id),
                "datasets": {},
            },
        )
        cfg_bucket["datasets"][dataset_id] = row

    wide_rows = sorted(
        by_config.values(),
        key=lambda r: str(r["short_config_id"]),
    )

    dataset_label_map = {
        "nersc_qa.v2": "QA",
        "ticket_cases": "Tickets",
    }

    lines: list[str] = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\caption{" + _escape_tex(args.caption) + "}")
    lines.append("\\label{" + _escape_tex(args.label) + "}")
    lines.append("\\centering")
    lines.append("\\begin{tabular}{l" + "rrrr" * len(dataset_order) + "}")
    lines.append("\\toprule")
    header = ["Config"]
    for dataset_id in dataset_order:
        dataset_label = dataset_label_map.get(dataset_id, dataset_id)
        header.append(f"\\multicolumn{{4}}{{c}}{{{_escape_tex(dataset_label)}}}")
    lines.append(" & ".join(header) + " \\\\")
    if dataset_order:
        cmidrules = []
        for idx in range(len(dataset_order)):
            start_col = 2 + (idx * 4)
            end_col = start_col + 3
            cmidrules.append(f"\\cmidrule(lr){{{start_col}-{end_col}}}")
        lines.append(" ".join(cmidrules))
    subheader = [""]
    for _ in dataset_order:
        subheader.append("Pass/Score")
        subheader.append("Fail")
        subheader.append("Tokens I/O/T")
        subheader.append("Lat")
    lines.append(" & ".join(subheader) + " \\\\")
    lines.append("\\midrule")
    for cfg in wide_rows:
        row_cells = [
            _escape_tex(str(cfg["short_config_id"])),
        ]
        for dataset_id in dataset_order:
            ds = cfg["datasets"].get(dataset_id, {})
            row_cells.append(_fmt_pass_score(ds.get("pass_rate"), ds.get("score_mean")))
            row_cells.append(_fmt_fail_count(ds.get("skipped_count")))
            row_cells.append(_fmt_tokens_iot(ds))
            row_cells.append(_fmt_latency_s(ds.get("latency_ms_p50")))
        lines.append(" & ".join(row_cells) + " \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")
    lines.append("")

    out_path = Path(args.output_tex)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))

    print(f"Wrote {out_path}")
    print(f"loaded_summaries={loaded_summaries}")
    print(f"skipped_non_aggregate_summaries={skipped_non_aggregate}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
