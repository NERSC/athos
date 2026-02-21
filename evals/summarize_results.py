#!/usr/bin/env python3
"""Summarize canonical runs and judgments into grouped aggregate metrics."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _discover_run_paths(runs_dir: str) -> list[Path]:
    return sorted(Path(runs_dir).glob("**/run.json"))


def _discover_judgment_paths(judgments_dir: str | None, judgments_files: list[str]) -> list[Path]:
    paths: list[Path] = []
    if judgments_dir:
        for path in sorted(Path(judgments_dir).glob("**/*.jsonl")):
            # Skip sidecar skip-detail files; only judgment JSONL files belong here.
            if path.name.endswith(".skips.jsonl"):
                continue
            paths.append(path)
    paths.extend(Path(item) for item in judgments_files)

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = str(path.resolve())
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)
    return deduped


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _stddev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mu = _mean(values)
    if mu is None:
        return None
    variance = sum((v - mu) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def _ci95(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    sigma = _stddev(values)
    if sigma is None:
        return None
    return 1.96 * sigma / math.sqrt(len(values))


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _prefer_judgment(existing: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    if existing is None:
        return candidate
    existing_dt = _parse_datetime(existing.get("scored_at_utc"))
    candidate_dt = _parse_datetime(candidate.get("scored_at_utc"))
    if existing_dt is None and candidate_dt is None:
        return candidate
    if existing_dt is None:
        return candidate
    if candidate_dt is None:
        return existing
    return candidate if candidate_dt >= existing_dt else existing


def _value_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _judgment_identity(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    return (
        _value_or_none(payload.get("judge_id")),
        _value_or_none(payload.get("judge_model")),
        _value_or_none(payload.get("judge_prompt_version")),
    )


def _parse_judgments(
    paths: list[Path],
    *,
    judge_id_filter: str | None,
    judge_model_filter: str | None,
    judge_prompt_version_filter: str | None,
    allow_mixed_judges: bool,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    tuple[str | None, str | None, str | None] | None,
    int,
]:
    by_run_id: dict[str, dict[str, Any]] = {}
    by_run_path: dict[str, dict[str, Any]] = {}
    seen_identities: set[tuple[str | None, str | None, str | None]] = set()
    for path in paths:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            judge_id, judge_model, judge_prompt_version = _judgment_identity(payload)
            if judge_id_filter and judge_id != judge_id_filter:
                continue
            if judge_model_filter and judge_model != judge_model_filter:
                continue
            if judge_prompt_version_filter and judge_prompt_version != judge_prompt_version_filter:
                continue
            seen_identities.add((judge_id, judge_model, judge_prompt_version))
            run_id = payload.get("run_id")
            if isinstance(run_id, str) and run_id:
                by_run_id[run_id] = _prefer_judgment(by_run_id.get(run_id), payload)
            run_path = payload.get("run_path")
            if isinstance(run_path, str) and run_path:
                resolved = str(Path(run_path).resolve())
                by_run_path[resolved] = _prefer_judgment(by_run_path.get(resolved), payload)
    if len(seen_identities) > 1 and not allow_mixed_judges:
        rendered = ", ".join(
            sorted(
                f"(judge_id={jid!r}, judge_model={jmodel!r}, judge_prompt_version={jprompt!r})"
                for jid, jmodel, jprompt in seen_identities
            )
        )
        raise ValueError(
            "Mixed judge identities found across judgments. "
            "Pass --judge-id (or --judge-model/--judge-prompt-version) to select one, "
            "or pass --allow-mixed-judges. "
            f"Found: {rendered}"
        )
    selected_identity = None
    if len(seen_identities) == 1:
        selected_identity = sorted(
            seen_identities, key=lambda x: (str(x[0]), str(x[1]), str(x[2]))
        )[-1]
    return by_run_id, by_run_path, selected_identity, len(seen_identities)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", required=True)
    parser.add_argument("--judgments-dir", default=None)
    parser.add_argument(
        "--judgment-file",
        action="append",
        default=[],
        help="Path to a judgments JSONL file (repeatable)",
    )
    parser.add_argument("--judge-id", default=None, help="Filter judgments by judge_id")
    parser.add_argument("--judge-model", default=None, help="Filter judgments by judge_model")
    parser.add_argument(
        "--judge-prompt-version",
        default=None,
        help="Filter judgments by judge_prompt_version",
    )
    parser.add_argument(
        "--allow-mixed-judges",
        action="store_true",
        help="Allow aggregating judgments from multiple judge identity tuples",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    run_paths = _discover_run_paths(args.runs_dir)
    if not run_paths:
        raise ValueError(f"No run.json files found under {args.runs_dir}")

    judgment_paths = _discover_judgment_paths(args.judgments_dir, args.judgment_file)
    (
        judgments_by_run_id,
        judgments_by_run_path,
        selected_identity,
        judge_identity_count,
    ) = _parse_judgments(
        judgment_paths,
        judge_id_filter=args.judge_id,
        judge_model_filter=args.judge_model,
        judge_prompt_version_filter=args.judge_prompt_version,
        allow_mixed_judges=args.allow_mixed_judges,
    )

    groups: dict[tuple[str, str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "run_count": 0,
            "scored_count": 0,
            "skipped_count": 0,
            "pass_count": 0,
            "scores": [],
            "skipped_by_reason": defaultdict(int),
        }
    )

    for run_path in run_paths:
        run_payload = json.loads(run_path.read_text())
        run_id = run_payload.get("run_id")
        key = (
            str(run_payload.get("experiment_id")),
            str(run_payload.get("agent_system")),
            str(run_payload.get("config_id")),
            str(run_payload.get("dataset_id")),
        )
        group = groups[key]
        group["run_count"] += 1

        judgment = None
        if isinstance(run_id, str) and run_id:
            judgment = judgments_by_run_id.get(run_id)
        else:
            judgment = judgments_by_run_path.get(str(run_path.resolve()))

        if isinstance(judgment, dict):
            judgment_status = judgment.get("judgment_status")
            if isinstance(judgment_status, str) and judgment_status.startswith("skipped_"):
                group["skipped_count"] += 1
                group["skipped_by_reason"][judgment_status] += 1
            score = judgment.get("score")
            passed = judgment.get("pass")
            if isinstance(score, (int, float)):
                group["scored_count"] += 1
                group["scores"].append(float(score))
            if isinstance(passed, bool) and passed:
                group["pass_count"] += 1

    aggregates: list[dict[str, Any]] = []
    for (experiment_id, agent_system, config_id, dataset_id), group in sorted(groups.items()):
        scores = group["scores"]
        scored_count = group["scored_count"]
        pass_count = group["pass_count"]
        aggregates.append(
            {
                "experiment_id": experiment_id,
                "agent_system": agent_system,
                "config_id": config_id,
                "dataset_id": dataset_id,
                "run_count": group["run_count"],
                "scored_count": scored_count,
                "skipped_count": group["skipped_count"],
                "skipped_by_reason": dict(group["skipped_by_reason"]),
                "score_mean": _mean(scores),
                "score_stddev": _stddev(scores),
                "score_ci95": _ci95(scores),
                "pass_rate": (pass_count / scored_count) if scored_count else None,
            }
        )

    payload = {
        "schema_version": "athos.summary.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runs_dir": args.runs_dir,
        "judgment_sources": [str(path) for path in judgment_paths],
        "judge_id": (
            selected_identity[0]
            if selected_identity
            else ("mixed" if judge_identity_count > 1 else args.judge_id)
        ),
        "judge_model": (
            selected_identity[1]
            if selected_identity
            else ("mixed" if judge_identity_count > 1 else args.judge_model)
        ),
        "judge_prompt_version": (
            selected_identity[2]
            if selected_identity
            else ("mixed" if judge_identity_count > 1 else args.judge_prompt_version)
        ),
        "judge_identity_count": judge_identity_count,
        "aggregates": aggregates,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))

    print(
        f"Wrote summary to {output_path} "
        f"(groups={len(aggregates)}, runs={len(run_paths)}, judgment_files={len(judgment_paths)})"
    )


if __name__ == "__main__":
    main()
