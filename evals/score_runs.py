#!/usr/bin/env python3
"""Score canonical run records and emit append-only judgments JSONL."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable
import uuid

from athos import build_config
from athos.frameworks.smolagents import factories as smolagents_factories

from eval_core import evaluate_response
from eval_io import load_qa_cases, load_test_cases


def _discover_run_paths(runs_dir: str | None, runs_manifest: str | None) -> list[Path]:
    run_paths: list[Path] = []
    if runs_dir:
        run_paths.extend(sorted(Path(runs_dir).glob("**/run.json")))

    if runs_manifest:
        for line in Path(runs_manifest).read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("{"):
                payload = json.loads(line)
                candidate = payload.get("path")
                if isinstance(candidate, str) and candidate:
                    run_paths.append(Path(candidate))
            else:
                run_paths.append(Path(line))

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in run_paths:
        resolved = str(path.resolve())
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)
    return deduped


def _build_reference_map(cases_dir: Iterable[str], qa_file: Iterable[str]) -> Dict[str, str]:
    refs: Dict[str, str] = {}
    for directory in cases_dir:
        for case in load_test_cases(Path(directory)):
            case_id = case.get("name")
            solution = case.get("solution")
            if isinstance(case_id, str) and isinstance(solution, str):
                refs[case_id] = solution

    for qa_path in qa_file:
        for case in load_qa_cases(Path(qa_path)):
            case_id = case.get("name")
            solution = case.get("solution")
            if isinstance(case_id, str) and isinstance(solution, str):
                refs[case_id] = solution
    return refs


def _resolve_reference(run_payload: dict, reference_map: Dict[str, str]) -> str | None:
    direct_reference = run_payload.get("reference")
    if isinstance(direct_reference, str) and direct_reference:
        return direct_reference

    request_payload = run_payload.get("request")
    if isinstance(request_payload, dict):
        reference_text = request_payload.get("reference_text")
        if isinstance(reference_text, str) and reference_text:
            return reference_text

    case_id = run_payload.get("case_id")
    if isinstance(case_id, str):
        return reference_map.get(case_id)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--runs-dir", default=None)
    parser.add_argument("--runs-manifest", default=None)
    parser.add_argument("--judge-model", required=True)
    parser.add_argument("--judge-prompt-version", default="v1")
    parser.add_argument("--judge-id", default=None)
    parser.add_argument("--passing-score", type=float, default=80.0)
    parser.add_argument(
        "--cases-dir",
        action="append",
        default=[],
        help="Directory containing test case subdirectories (can be used multiple times)",
    )
    parser.add_argument(
        "--qa-file",
        action="append",
        default=[],
        help="JSON Lines file with question/answer pairs (can be used multiple times)",
    )
    parser.add_argument("--output", required=True, help="Judgments JSONL output file path")
    args = parser.parse_args()

    if not args.runs_dir and not args.runs_manifest:
        raise ValueError("One of --runs-dir or --runs-manifest is required")

    if not args.cases_dir and not args.qa_file:
        args.cases_dir = ["evals/test_cases"]

    run_paths = _discover_run_paths(args.runs_dir, args.runs_manifest)
    if not run_paths:
        raise ValueError("No run files found to score")

    cfg = build_config(args.config)
    if args.judge_model not in cfg.models:
        raise ValueError(f"Judge model '{args.judge_model}' not found in config models")
    judge_model_instance = smolagents_factories.build_model(cfg.models[args.judge_model])
    judge_id = args.judge_id or f"{args.judge_model}:{args.judge_prompt_version}"

    reference_map = _build_reference_map(args.cases_dir, args.qa_file)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scored_count = 0
    skipped_count = 0
    with output_path.open("a", encoding="utf-8") as handle:
        for run_path in run_paths:
            run_payload = json.loads(run_path.read_text())
            run_id = run_payload.get("run_id")
            if not isinstance(run_id, str) or not run_id:
                skipped_count += 1
                continue

            response_payload = run_payload.get("response")
            output_text = None
            if isinstance(response_payload, dict):
                output_text = response_payload.get("output_text")

            reference = _resolve_reference(run_payload, reference_map)

            score = None
            feedback = "Skipped: missing reference or response output."
            passed = None
            if isinstance(reference, str) and reference and isinstance(output_text, str) and output_text:
                score, feedback = evaluate_response(judge_model_instance, reference, output_text)
                if isinstance(score, (int, float)):
                    passed = score >= args.passing_score
                scored_count += 1
            else:
                skipped_count += 1

            judgment = {
                "schema_version": "athos.judgment.v1",
                "score_id": str(uuid.uuid4()),
                "run_id": run_id,
                "judge_id": judge_id,
                "judge_model": args.judge_model,
                "judge_prompt_version": args.judge_prompt_version,
                "scored_at_utc": datetime.now(timezone.utc).isoformat(),
                "score": float(score) if isinstance(score, (int, float)) else None,
                "pass": passed,
                "rationale": feedback,
                "subscores": {},
            }
            handle.write(json.dumps(judgment) + "\n")

    print(
        f"Wrote judgments to {output_path} "
        f"(scored={scored_count}, skipped={skipped_count}, total={len(run_paths)})"
    )


if __name__ == "__main__":
    main()
