#!/usr/bin/env python3
"""Summarize the completed human audit worksheet for the CUG paper."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def pct(n: int, d: int) -> str:
    if d == 0:
        return "n/a"
    return f"{(100.0 * n / d):.1f}%"


def summarize(rows: list[dict[str, str]]) -> str:
    filled = [r for r in rows if r.get("agreement", "").strip()]
    agree = sum(r["agreement"].strip() == "agree" for r in filled)
    disagree = sum(r["agreement"].strip() == "disagree" for r in filled)

    lines: list[str] = []
    lines.append(f"rows_total={len(rows)}")
    lines.append(f"rows_completed={len(filled)}")
    lines.append(f"overall_agreement={agree}/{len(filled)} ({pct(agree, len(filled))})")
    lines.append(f"overall_disagreement={disagree}/{len(filled)} ({pct(disagree, len(filled))})")
    lines.append("")

    for field in ("dataset", "stratum"):
        lines.append(f"by_{field}:")
        values = sorted({r[field] for r in filled})
        for value in values:
            subset = [r for r in filled if r[field] == value]
            a = sum(r["agreement"].strip() == "agree" for r in subset)
            lines.append(f"  {value}: {a}/{len(subset)} ({pct(a, len(subset))})")
        lines.append("")

    rationale_quality = Counter(
        r["judge_rationale_quality"].strip()
        for r in filled
        if r.get("judge_rationale_quality", "").strip()
    )
    disagreement_type = Counter(
        r["disagreement_type"].strip()
        for r in filled
        if r.get("disagreement_type", "").strip()
    )

    lines.append("judge_rationale_quality:")
    for key, value in rationale_quality.most_common():
        lines.append(f"  {key}: {value}")
    lines.append("")

    lines.append("disagreement_type_counts:")
    for key, value in disagreement_type.most_common():
        lines.append(f"  {key}: {value}")
    lines.append("")

    lines.append("disagreement_rows:")
    for r in filled:
        if r["agreement"].strip() != "disagree":
            continue
        lines.append(
            "  "
            + " | ".join(
                [
                    r["config"],
                    r["dataset"],
                    r["stratum"],
                    r["case_id"],
                    f"judge={r['judge_score']}:{r['judge_pass']}",
                    f"human={r['human_pass']}",
                    f"type={r['disagreement_type'] or 'n/a'}",
                ]
            )
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worksheet",
        default="docs/cug_paper/human_audit_review_sheet.csv",
        help="Path to the completed audit worksheet CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    worksheet = Path(args.worksheet)
    with worksheet.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    print(summarize(rows))


if __name__ == "__main__":
    main()
