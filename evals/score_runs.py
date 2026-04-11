#!/usr/bin/env python3
"""Score canonical run records and emit append-only judgments JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable
import uuid

from dotenv import load_dotenv

from athos import build_config
from athos.frameworks.smolagents import factories as smolagents_factories

from eval_core import evaluate_response
from eval_io import load_qa_cases, load_test_cases


UPSTREAM_ERROR_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bbad gateway\b|\b502\b"), "http_502"),
    (re.compile(r"\bservice unavailable\b|\b503\b"), "http_503"),
    (
        re.compile(
            r"\b504\b|\bgateway(?:\s+time(?:\s*out|-out)?|\s+timeout)\b|"
            r"\berror code\s*:?[\s'\"]*504\b"
        ),
        "http_504",
    ),
    (re.compile(r"\bupstream connect error\b"), "upstream_connect_error"),
    (re.compile(r"\btemporarily unavailable\b"), "upstream_unavailable"),
)
UPSTREAM_ERROR_CODES = {
    error_code for _, error_code in UPSTREAM_ERROR_PATTERNS
}


def _normalize_error_text(text: str | None) -> str:
    if not isinstance(text, str):
        return ""
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return lowered.strip()


def _detect_upstream_error_code(text: str | None) -> str | None:
    normalized = _normalize_error_text(text)
    if not normalized:
        return None
    for pattern, error_code in UPSTREAM_ERROR_PATTERNS:
        if pattern.search(normalized):
            return error_code
    return None


def _looks_like_error_output(text: str | None) -> bool:
    if not isinstance(text, str):
        return False
    lowered = text.lower().strip()
    if lowered.startswith("error:"):
        return True
    if lowered.startswith("exception:"):
        return True
    if lowered.startswith("traceback"):
        return True
    if "<html" in lowered and (
        "gateway time-out" in lowered
        or "gateway timeout" in lowered
        or "bad gateway" in lowered
        or "service unavailable" in lowered
    ):
        return True
    return False


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


def _build_reference_map(
    cases_dir: Iterable[str], qa_file: Iterable[str]
) -> tuple[Dict[tuple[str, str], str], Dict[str, str | None]]:
    refs_by_dataset_case: Dict[tuple[str, str], str] = {}
    refs_by_case: Dict[str, str | None] = {}

    def _update_fallback(case_id: str, solution: str) -> None:
        if case_id not in refs_by_case:
            refs_by_case[case_id] = solution
            return
        existing = refs_by_case[case_id]
        if existing is None:
            return
        if existing != solution:
            refs_by_case[case_id] = None

    for directory in cases_dir:
        dataset_id = Path(directory).name
        for case in load_test_cases(Path(directory)):
            case_id = case.get("name")
            solution = case.get("solution")
            if isinstance(case_id, str) and isinstance(solution, str):
                refs_by_dataset_case[(dataset_id, case_id)] = solution
                _update_fallback(case_id, solution)

    for qa_path in qa_file:
        dataset_id = Path(qa_path).stem
        for case in load_qa_cases(Path(qa_path)):
            case_id = case.get("name")
            solution = case.get("solution")
            if isinstance(case_id, str) and isinstance(solution, str):
                refs_by_dataset_case[(dataset_id, case_id)] = solution
                _update_fallback(case_id, solution)
    return refs_by_dataset_case, refs_by_case


def _resolve_reference(
    run_payload: dict,
    reference_map: Dict[tuple[str, str], str],
    fallback_case_map: Dict[str, str | None],
) -> str | None:
    direct_reference = run_payload.get("reference")
    if isinstance(direct_reference, str) and direct_reference:
        return direct_reference

    request_payload = run_payload.get("request")
    if isinstance(request_payload, dict):
        reference_text = request_payload.get("reference_text")
        if isinstance(reference_text, str) and reference_text:
            return reference_text

    case_id = run_payload.get("case_id")
    dataset_id = run_payload.get("dataset_id")
    if isinstance(dataset_id, str) and isinstance(case_id, str):
        return reference_map.get((dataset_id, case_id))
    if isinstance(case_id, str):
        return fallback_case_map.get(case_id)
    return None


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--runs-dir", default=None)
    parser.add_argument("--runs-manifest", default=None)
    parser.add_argument("--judge-model", required=True)
    parser.add_argument("--judge-prompt-version", default="v1")
    parser.add_argument("--judge-id", default=None)
    parser.add_argument("--passing-score", type=float, default=80.0)
    parser.add_argument(
        "--judge-max-attempts",
        type=int,
        default=3,
        help="Maximum attempts per run when judge output is non-numeric or judge call fails.",
    )
    parser.add_argument(
        "--judge-retry-delay-ms",
        type=int,
        default=0,
        help="Delay between judge retry attempts in milliseconds.",
    )
    parser.add_argument(
        "--fail-on-skip",
        action="store_true",
        help="Exit non-zero if any run cannot be scored",
    )
    parser.add_argument(
        "--skips-output",
        default=None,
        help="Optional JSONL file to write detailed skip records",
    )
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
    parser.add_argument(
        "--progress-every",
        type=int,
        default=25,
        help="Emit progress log every N runs processed (0 disables periodic logs).",
    )
    args = parser.parse_args()

    if not args.runs_dir and not args.runs_manifest:
        raise ValueError("One of --runs-dir or --runs-manifest is required")
    if args.judge_max_attempts < 1:
        raise ValueError("--judge-max-attempts must be >= 1")
    if args.judge_retry_delay_ms < 0:
        raise ValueError("--judge-retry-delay-ms must be >= 0")

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
    judge_cfg = cfg.models[args.judge_model]

    print(
        "Scoring config: "
        f"runs={len(run_paths)} "
        f"judge_model={args.judge_model} "
        f"judge_id={judge_id} "
        f"model_id={getattr(judge_cfg, 'model_id', None)} "
        f"api_base={getattr(judge_cfg, 'api_base', None)} "
        f"output={args.output} "
        f"skips_output={args.skips_output}",
        flush=True,
    )

    reference_map, fallback_case_map = _build_reference_map(args.cases_dir, args.qa_file)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    skips_output_path = Path(args.skips_output) if args.skips_output else None
    if skips_output_path:
        skips_output_path.parent.mkdir(parents=True, exist_ok=True)

    scored_count = 0
    zero_scored_failure_count = 0
    skipped_count = 0
    skipped_reasons: dict[str, int] = {}
    skips: list[dict] = []
    started_at = time.time()

    def _record_skip(
        *,
        run_path: Path,
        run_id: str | None,
        reason: str,
        detail: str,
        case_id: str | None = None,
    ) -> None:
        nonlocal skipped_count
        skipped_count += 1
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        if skips_output_path:
            skips.append(
                {
                    "schema_version": "athos.skip.v1",
                    "run_id": run_id,
                    "case_id": case_id,
                    "run_path": str(run_path),
                    "reason": reason,
                    "detail": detail,
                    "skipped_at_utc": datetime.now(timezone.utc).isoformat(),
                }
            )

    write_count = 0
    temp_fd, temp_output_str = tempfile.mkstemp(
        dir=output_path.parent,
        prefix=output_path.stem + ".",
        suffix=".tmp",
    )
    temp_output_path = Path(temp_output_str)
    with os.fdopen(temp_fd, "w", encoding="utf-8") as handle:
        for idx, run_path in enumerate(run_paths, start=1):
            run_payload = json.loads(run_path.read_text())
            run_id = run_payload.get("run_id")
            run_path_str = str(run_path.resolve())
            case_id = run_payload.get("case_id") if isinstance(run_payload.get("case_id"), str) else None
            run_id_for_judgment = run_id if isinstance(run_id, str) and run_id else None
            if run_id_for_judgment is None:
                digest = hashlib.sha1(run_path_str.encode("utf-8")).hexdigest()[:12]
                run_id_for_judgment = f"missing_run_id:{digest}"

            response_payload = run_payload.get("response")
            output_text = None
            if isinstance(response_payload, dict):
                output_text = response_payload.get("output_text")
            output_text_present = isinstance(output_text, str) and bool(output_text.strip())

            reference = _resolve_reference(run_payload, reference_map, fallback_case_map)
            execution_payload = run_payload.get("execution")
            execution_status = "success"
            execution_error_type = None
            execution_error_message = None
            if isinstance(execution_payload, dict):
                status_value = execution_payload.get("status")
                if isinstance(status_value, str) and status_value:
                    execution_status = status_value
                error_type_value = execution_payload.get("error_type")
                if isinstance(error_type_value, str) and error_type_value:
                    execution_error_type = error_type_value
                error_message_value = execution_payload.get("error_message")
                if isinstance(error_message_value, str) and error_message_value:
                    execution_error_message = error_message_value

            # Legacy fallback: older run records may be incorrectly marked success
            # even when they contain explicit upstream provider errors.
            if execution_status == "success":
                status_from_error_type = (
                    execution_error_type
                    if execution_error_type in UPSTREAM_ERROR_CODES
                    else None
                )
                status_from_error_message = _detect_upstream_error_code(execution_error_message)
                status_from_output = None
                if _looks_like_error_output(output_text):
                    status_from_output = _detect_upstream_error_code(output_text)
                upstream_code = (
                    status_from_error_type
                    or status_from_error_message
                    or status_from_output
                )
                if upstream_code:
                    execution_status = "upstream_error"

            score = None
            feedback = None
            passed = None
            judgment_status = "scored"
            if not (isinstance(run_id, str) and run_id):
                judgment_status = "skipped_invalid_run"
                feedback = "Skipped: missing required run_id."
                score = 0.0
                passed = False
                zero_scored_failure_count += 1
                _record_skip(
                    run_path=run_path,
                    run_id=run_id_for_judgment,
                    case_id=case_id,
                    reason=judgment_status,
                    detail=feedback,
                )
            elif execution_status == "upstream_error":
                judgment_status = "skipped_upstream_error"
                feedback = "Skipped: upstream gateway/provider failure (retryable)."
                score = 0.0
                passed = False
                zero_scored_failure_count += 1
                _record_skip(
                    run_path=run_path,
                    run_id=run_id_for_judgment,
                    case_id=case_id,
                    reason=judgment_status,
                    detail=feedback,
                )
            elif execution_status != "success":
                judgment_status = "skipped_execution_status"
                feedback = f"Skipped: execution status={execution_status}."
                score = 0.0
                passed = False
                zero_scored_failure_count += 1
                _record_skip(
                    run_path=run_path,
                    run_id=run_id_for_judgment,
                    case_id=case_id,
                    reason=judgment_status,
                    detail=feedback,
                )
            elif isinstance(reference, str) and reference and output_text_present:
                final_score = None
                final_feedback = None
                last_error_detail = None
                for attempt in range(1, args.judge_max_attempts + 1):
                    try:
                        score, feedback = evaluate_response(
                            judge_model_instance, reference, output_text
                        )
                    except Exception as exc:  # pragma: no cover - passthrough safety
                        score = None
                        feedback = None
                        last_error_detail = (
                            f"attempt={attempt}/{args.judge_max_attempts} "
                            f"judge_exception={type(exc).__name__}: {exc}"
                        )
                    else:
                        final_feedback = feedback
                        if isinstance(score, (int, float)) and not isinstance(score, bool):
                            final_score = float(score)
                            break
                        last_error_detail = (
                            f"attempt={attempt}/{args.judge_max_attempts} "
                            f"non_numeric_score={score!r}"
                        )
                        print(
                            f"[judge-retry] run={idx}/{len(run_paths)} "
                            f"case_id={case_id or '<unknown>'} "
                            f"attempt={attempt}/{args.judge_max_attempts} "
                            f"detail={last_error_detail}",
                            flush=True,
                        )
                    if last_error_detail and attempt == args.judge_max_attempts:
                        print(
                            f"[judge-failed] run={idx}/{len(run_paths)} "
                            f"case_id={case_id or '<unknown>'} "
                            f"detail={last_error_detail}",
                            flush=True,
                        )

                    if (
                        attempt < args.judge_max_attempts
                        and args.judge_retry_delay_ms > 0
                    ):
                        time.sleep(args.judge_retry_delay_ms / 1000)

                if final_score is not None:
                    score = final_score
                    feedback = final_feedback
                    passed = score >= args.passing_score
                    scored_count += 1
                else:
                    judgment_status = "skipped_judge_error"
                    feedback = (
                        "Skipped: judge output invalid after retries. "
                        f"{last_error_detail}"
                    )
                    score = 0.0
                    passed = False
                    zero_scored_failure_count += 1
                    _record_skip(
                        run_path=run_path,
                        run_id=run_id_for_judgment,
                        case_id=case_id,
                        reason=judgment_status,
                        detail=feedback,
                    )
            else:
                if not (isinstance(reference, str) and reference):
                    judgment_status = "skipped_missing_reference"
                    feedback = "Skipped: missing reference."
                elif not output_text_present:
                    judgment_status = "skipped_missing_output"
                    feedback = "Skipped: missing response output."
                else:
                    judgment_status = "skipped_invalid_run"
                    feedback = "Skipped: invalid run payload."
                score = 0.0
                passed = False
                zero_scored_failure_count += 1
                _record_skip(
                    run_path=run_path,
                    run_id=run_id,
                    case_id=case_id,
                    reason=judgment_status,
                    detail=feedback,
                )

            judgment = {
                "schema_version": "athos.judgment.v1",
                "score_id": str(uuid.uuid4()),
                "run_id": run_id_for_judgment,
                "run_path": run_path_str,
                "judge_id": judge_id,
                "judge_model": args.judge_model,
                "judge_prompt_version": args.judge_prompt_version,
                "scored_at_utc": datetime.now(timezone.utc).isoformat(),
                "judgment_status": judgment_status,
                "score": float(score) if isinstance(score, (int, float)) else None,
                "pass": passed,
                "rationale": feedback,
                "subscores": {},
            }
            handle.write(json.dumps(judgment) + "\n")
            write_count += 1
            if args.progress_every and (
                idx == 1 or idx == len(run_paths) or idx % args.progress_every == 0
            ):
                elapsed = time.time() - started_at
                print(
                    f"[progress] processed={idx}/{len(run_paths)} "
                    f"scored={scored_count} "
                    f"skipped={skipped_count} "
                    f"last_status={judgment_status} "
                    f"last_case={case_id or '<unknown>'} "
                    f"elapsed_s={elapsed:.1f}",
                    flush=True,
                )

        handle.flush()
        os.fsync(handle.fileno())
    temp_output_path.replace(output_path)

    if skips_output_path:
        skip_fd, skip_temp_str = tempfile.mkstemp(
            dir=skips_output_path.parent,
            prefix=skips_output_path.stem + ".",
            suffix=".tmp",
        )
        skip_temp_path = Path(skip_temp_str)
        try:
            with os.fdopen(skip_fd, "w", encoding="utf-8") as skip_handle:
                for skip in skips:
                    skip_handle.write(json.dumps(skip) + "\n")
                skip_handle.flush()
                os.fsync(skip_handle.fileno())
            skip_temp_path.replace(skips_output_path)
        except BaseException:
            skip_temp_path.unlink(missing_ok=True)
            raise

    try:
        output_size = output_path.stat().st_size
    except FileNotFoundError:
        output_size = None
    print(
        f"Judgment file stats: path={output_path} "
        f"writes={write_count} size_bytes={output_size}"
    )

    print(
        f"Wrote judgments to {output_path} "
        f"(scored={scored_count}, zero_scored_failures={zero_scored_failure_count}, "
        f"skipped={skipped_count}, total={len(run_paths)}, "
        f"skip_reasons={skipped_reasons})",
        flush=True,
    )

    if args.fail_on_skip and skipped_count > 0:
        raise SystemExit(
            f"Scoring encountered {skipped_count} skipped runs (fail-on-skip enabled)."
        )


if __name__ == "__main__":
    main()
