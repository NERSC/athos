#!/usr/bin/env python3
"""Render a LaTeX table for the focused harness comparison study."""

from __future__ import annotations

import argparse
import json
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


def _fmt_pass_score(row: dict[str, Any]) -> str:
    return f"{_fmt_pct(row.get('pass_rate'))} / {_fmt_score(row.get('score_mean'))}"


def _fmt_tokens_iot(row: dict[str, Any]) -> str:
    def _tok(value: Any) -> str:
        if isinstance(value, (int, float)):
            return f"{float(value) / 1000.0:.1f}k"
        return "N/A"

    return (
        f"{_tok(row.get('tokens_input_mean'))}/"
        f"{_tok(row.get('tokens_output_mean'))}/"
        f"{_tok(row.get('tokens_total_mean'))}"
    )


def _fmt_latency(row: dict[str, Any]) -> str:
    value = row.get("latency_ms_p50")
    if isinstance(value, (int, float)):
        return f"{float(value) / 1000.0:.1f}s"
    return "N/A"


def _row_identity(config_id: str) -> tuple[str, str]:
    harness = "LangChain" if "cug_lang_" in config_id else "SmolAgents"
    model = "Claude Sonnet" if "sonnet" in config_id else "GPT-OSS"
    return harness, model


def _sort_key(config_id: str) -> tuple[int, int]:
    harness_order = 0 if "cug_lang_" in config_id else 1
    model_order = 0 if "gptoss" in config_id else 1
    return harness_order, model_order


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--output-tex", required=True)
    parser.add_argument(
        "--caption",
        default=(
            "Focused Harness Comparison on Auxiliary Small-Scale Q\\&A and Ticket Sets "
            "(Tokens I/O/T = mean input/output/total tokens per run; Lat = median end-to-end latency)."
        ),
    )
    parser.add_argument("--label", default="tab:cug-harness-comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(Path(args.summary_json).read_text())
    aggregates = payload.get("aggregates", [])

    wanted_datasets = ["simple_qa", "test_cases"]
    rows_by_config: dict[str, dict[str, dict[str, Any]]] = {}
    for row in aggregates:
        if not isinstance(row, dict):
            continue
        dataset_id = str(row.get("dataset_id", ""))
        if dataset_id not in wanted_datasets:
            continue
        config_id = str(row.get("config_id", ""))
        if not config_id:
            continue
        rows_by_config.setdefault(config_id, {})[dataset_id] = row

    config_ids = sorted(rows_by_config, key=_sort_key)

    lines: list[str] = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\caption{" + args.caption + "}")
    lines.append("\\label{" + args.label + "}")
    lines.append("\\centering")
    lines.append("\\begin{tabular}{llrrrrrr}")
    lines.append("\\toprule")
    lines.append(
        "Harness & Model & "
        "\\multicolumn{3}{c}{Q\\&A-S} & "
        "\\multicolumn{3}{c}{Ticket-S} \\\\"
    )
    lines.append("\\cmidrule(lr){3-5} \\cmidrule(lr){6-8}")
    lines.append(
        " & & Pass/Score & Tokens I/O/T & Lat & "
        "Pass/Score & Tokens I/O/T & Lat \\\\"
    )
    lines.append("\\midrule")

    for config_id in config_ids:
        harness, model = _row_identity(config_id)
        simple_qa = rows_by_config[config_id].get("simple_qa", {})
        test_cases = rows_by_config[config_id].get("test_cases", {})
        lines.append(
            " & ".join(
                [
                    _escape_tex(harness),
                    _escape_tex(model),
                    _fmt_pass_score(simple_qa),
                    _fmt_tokens_iot(simple_qa),
                    _fmt_latency(simple_qa),
                    _fmt_pass_score(test_cases),
                    _fmt_tokens_iot(test_cases),
                    _fmt_latency(test_cases),
                ]
            )
            + " \\\\"
        )

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")
    lines.append("")

    out_path = Path(args.output_tex)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
