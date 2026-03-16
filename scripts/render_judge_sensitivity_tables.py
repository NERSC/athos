#!/usr/bin/env python3
"""Render lightweight judge-sensitivity LaTeX tables from per-judge summaries."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pick_better(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    ex_scored = existing.get("scored_count")
    ca_scored = candidate.get("scored_count")
    if isinstance(ex_scored, int) and isinstance(ca_scored, int):
        if ca_scored > ex_scored:
            return candidate
        if ex_scored > ca_scored:
            return existing
    ex_ts = _parse_ts(existing.get("_summary_generated_at_utc"))
    ca_ts = _parse_ts(candidate.get("_summary_generated_at_utc"))
    if ex_ts is None:
        return candidate
    if ca_ts is None:
        return existing
    return candidate if ca_ts >= ex_ts else existing


def _short_config_id(config_id: str) -> str:
    harness = "lang" if ("_lang_" in config_id or config_id.startswith("cug_lang_")) else "smol"
    model = "sonnet" if "sonnet" in config_id else ("gptoss" if "gptoss" in config_id else "unknown")
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary-root",
        required=True,
        help="Root dir containing per-judge summary subdirs.",
    )
    parser.add_argument(
        "--judge",
        action="append",
        required=True,
        help="Judge model key (repeatable). Example: gptoss",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for rendered LaTeX tables.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary_root = Path(args.summary_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    judge_labels = {
        "gptoss": "GPT-OSS",
        "llama_4_maverick": "Llama 4 Maverick",
        "mistral_large_3": "Mistral Large 3",
    }

    rows_by_judge: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for judge in args.judge:
        judge_dir = summary_root / judge
        if not judge_dir.exists():
            raise SystemExit(f"Missing judge summary dir: {judge_dir}")
        rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for path in sorted(judge_dir.glob("summary_*.json")):
            payload = json.loads(path.read_text())
            generated_at = payload.get("generated_at_utc")
            for row in payload.get("aggregates", []):
                if not isinstance(row, dict):
                    continue
                item = dict(row)
                item["_summary_generated_at_utc"] = generated_at
                key = (str(item.get("config_id", "")), str(item.get("dataset_id", "")))
                existing = rows_by_key.get(key)
                rows_by_key[key] = item if existing is None else _pick_better(existing, item)
        rows_by_judge[judge] = rows_by_key

    configs = sorted(
        {
            cfg
            for judge in args.judge
            for (cfg, _dataset) in rows_by_judge[judge].keys()
            if cfg
        }
    )

    combined: dict[str, dict[str, dict[str, Any]]] = {judge: {} for judge in args.judge}
    for judge in args.judge:
        for cfg in configs:
            rows = [row for (config_id, _), row in rows_by_judge[judge].items() if config_id == cfg]
            if not rows:
                continue
            score_num = 0.0
            pass_num = 0.0
            weight = 0
            scored_total = 0
            skipped_total = 0
            for row in rows:
                scored_count = row.get("scored_count")
                if not isinstance(scored_count, int):
                    scored_count = 0
                score_mean = row.get("score_mean")
                pass_rate = row.get("pass_rate")
                if scored_count > 0 and isinstance(score_mean, (int, float)):
                    score_num += float(score_mean) * scored_count
                    weight += scored_count
                if scored_count > 0 and isinstance(pass_rate, (int, float)):
                    pass_num += float(pass_rate) * scored_count
                scored_total += scored_count
                skipped_count = row.get("skipped_count")
                if isinstance(skipped_count, int):
                    skipped_total += skipped_count
            combined[judge][cfg] = {
                "score_mean": (score_num / weight) if weight > 0 else None,
                "pass_rate": (pass_num / weight) if weight > 0 else None,
                "scored_total": scored_total,
                "skipped_total": skipped_total,
            }

    # Output 1: leniency ladder.
    judge_totals: list[tuple[str, float, float, int, int]] = []
    for judge in args.judge:
        rows = list(combined[judge].values())
        scored = sum(int(row.get("scored_total", 0) or 0) for row in rows)
        skipped = sum(int(row.get("skipped_total", 0) or 0) for row in rows)
        weight = sum(
            int(row.get("scored_total", 0) or 0)
            for row in rows
            if isinstance(row.get("score_mean"), (int, float))
        )
        if weight <= 0:
            continue
        score = sum(
            float(row["score_mean"]) * int(row.get("scored_total", 0) or 0)
            for row in rows
            if isinstance(row.get("score_mean"), (int, float))
        ) / weight
        pr = sum(
            float(row["pass_rate"]) * int(row.get("scored_total", 0) or 0)
            for row in rows
            if isinstance(row.get("pass_rate"), (int, float))
        ) / weight
        judge_totals.append((judge, score, pr, scored, skipped))
    judge_totals.sort(key=lambda item: item[1])  # strict->lenient by score mean.

    lines = [
        "\\begin{table}[t]",
        "\\caption{Judge Leniency Ladder on Paper-Scope Main Results (weighted by scored runs across included configurations and datasets).}",
        "\\label{tab:cug-judge-leniency}",
        "\\centering",
        "\\begin{tabular}{lrrr}",
        "\\toprule",
        "Judge & Score Mean & Pass Rate & Scored \\\\",
        "\\midrule",
    ]
    for judge, score, pr, scored, skipped in judge_totals:
        label = judge_labels.get(judge, judge)
        lines.append(f"{_escape_tex(label)} & {_fmt_score(score)} & {_fmt_pct(pr)} & {scored} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    (output_dir / "cug_judge_leniency_ladder.tex").write_text("\n".join(lines))

    # Rank by combined score mean.
    ranks: dict[str, dict[str, int]] = {judge: {} for judge in args.judge}
    for judge in args.judge:
        ranked = sorted(
            [
                (metrics.get("score_mean"), cfg)
                for cfg, metrics in combined[judge].items()
                if isinstance(metrics.get("score_mean"), (int, float))
            ],
            reverse=True,
        )
        for idx, (_, cfg) in enumerate(ranked, start=1):
            ranks[judge][cfg] = idx

    cfg_order = sorted(configs, key=lambda cfg: ranks.get("llama_4_maverick", {}).get(cfg, 999))

    # Output 2: ranking stability.
    lines = [
        "\\begin{table*}[t]",
        "\\caption{Ranking Stability Across Judges for Main Paper Configurations (ranked by combined score mean; lower rank is better).}",
        "\\label{tab:cug-judge-ranking-stability}",
        "\\centering",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Config & GPT-OSS Rank & Maverick Rank & Mistral Rank & GPT-OSS Score & Maverick Score & Mistral Score \\\\",
        "\\midrule",
    ]
    for cfg in cfg_order:
        g = combined.get("gptoss", {}).get(cfg, {})
        l = combined.get("llama_4_maverick", {}).get(cfg, {})
        m = combined.get("mistral_large_3", {}).get(cfg, {})
        lines.append(
            " & ".join(
                [
                    _escape_tex(_short_config_id(cfg)),
                    str(ranks.get("gptoss", {}).get(cfg, "-")),
                    str(ranks.get("llama_4_maverick", {}).get(cfg, "-")),
                    str(ranks.get("mistral_large_3", {}).get(cfg, "-")),
                    _fmt_score(g.get("score_mean")),
                    _fmt_score(l.get("score_mean")),
                    _fmt_score(m.get("score_mean")),
                ]
            )
            + " \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""]
    (output_dir / "cug_judge_ranking_stability.tex").write_text("\n".join(lines))

    # Output 3: deltas vs Maverick.
    lines = [
        "\\begin{table*}[t]",
        "\\caption{Judge Delta View Relative to Maverick (main paper configurations; combined across datasets).}",
        "\\label{tab:cug-judge-deltas}",
        "\\centering",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Config & Maverick Score & Maverick Pass & $\\Delta$Score (GPT-OSS) & $\\Delta$Pass (GPT-OSS) & $\\Delta$Score (Mistral) & $\\Delta$Pass (Mistral) \\\\",
        "\\midrule",
    ]
    for cfg in cfg_order:
        l = combined.get("llama_4_maverick", {}).get(cfg, {})
        g = combined.get("gptoss", {}).get(cfg, {})
        m = combined.get("mistral_large_3", {}).get(cfg, {})
        l_score = l.get("score_mean")
        l_pass = l.get("pass_rate")
        g_score = g.get("score_mean")
        g_pass = g.get("pass_rate")
        m_score = m.get("score_mean")
        m_pass = m.get("pass_rate")
        if not all(isinstance(v, (int, float)) for v in [l_score, l_pass, g_score, g_pass, m_score, m_pass]):
            continue
        ds_g = float(g_score) - float(l_score)
        dp_g = (float(g_pass) - float(l_pass)) * 100.0
        ds_m = float(m_score) - float(l_score)
        dp_m = (float(m_pass) - float(l_pass)) * 100.0
        lines.append(
            " & ".join(
                [
                    _escape_tex(_short_config_id(cfg)),
                    _fmt_score(l_score),
                    _fmt_pct(l_pass),
                    f"{ds_g:+.1f}",
                    f"{dp_g:+.1f}pp",
                    f"{ds_m:+.1f}",
                    f"{dp_m:+.1f}pp",
                ]
            )
            + " \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""]
    (output_dir / "cug_judge_deltas.tex").write_text("\n".join(lines))

    print(f"Wrote {output_dir / 'cug_judge_leniency_ladder.tex'}")
    print(f"Wrote {output_dir / 'cug_judge_ranking_stability.tex'}")
    print(f"Wrote {output_dir / 'cug_judge_deltas.tex'}")


if __name__ == "__main__":
    main()
