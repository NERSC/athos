#!/usr/bin/env python3
"""Evaluation script for ATHOS flows on test cases"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import pprint
import re
import shlex
import socket
import subprocess
from datetime import datetime, timezone
import sys
import uuid

from dotenv import load_dotenv

from athos import build_config
from athos.models.enums import ExecutionMode
from athos.models.metrics import ExecutionMetrics
from athos.runtime.runner import FlowRunner

from eval_io import build_input, load_qa_cases, load_test_cases


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unknown"


def _compute_config_id(flow_name: str, flow_config) -> str:
    normalized_config = flow_config.model_dump()
    payload = json.dumps(normalized_config, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    model_name = _slug(str(normalized_config.get("model", "unknown")))
    return f"{_slug(flow_name)}__{model_name}__{digest}"


def _status_from_exception(error: Exception) -> str:
    if isinstance(error, TimeoutError):
        return "timeout"
    error_name = error.__class__.__name__.lower()
    if "timeout" in error_name:
        return "timeout"
    return "execution_error"


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--flow",
        nargs="+",
        required=True,
        help="One or more flow names to evaluate",
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
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file for results JSON",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for canonical per-run run.json artifacts",
    )
    parser.add_argument(
        "--experiment-id",
        default=None,
        help="Experiment ID used in canonical run artifact paths",
    )
    parser.add_argument(
        "--agent-system",
        default="athos",
        help="Agent system name for canonical run artifacts",
    )
    parser.add_argument(
        "--run-count",
        type=int,
        default=1,
        help="Number of repeated runs to execute per case",
    )
    parser.add_argument(
        "--run-start",
        type=int,
        default=0,
        help="Starting run index for canonical per-run artifacts",
    )
    parser.add_argument(
        "--allow-overwrite-runs",
        action="store_true",
        help="Allow overwriting existing canonical run.json artifacts",
    )
    args = parser.parse_args()
    load_dotenv()

    if args.run_count < 1:
        raise ValueError("--run-count must be >= 1")
    if args.run_start < 0:
        raise ValueError("--run-start must be >= 0")
    if args.output_dir and not args.experiment_id:
        raise ValueError("--experiment-id is required when --output-dir is set")

    if not args.cases_dir and not args.qa_file:
        args.cases_dir = ["evals/test_cases"]

    cfg = build_config(args.config)
    try:
        git_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).resolve().parent.parent,
            )
            .decode("utf-8")
            .strip()
        )
    except Exception:
        git_sha = None
    for name in args.flow:
        if name not in cfg.flows:
            raise ValueError(f"Flow '{name}' not found in config")

    runner = FlowRunner(cfg)
    print("Loaded flows:")
    print(args.flow)

    datasets = []
    for d in args.cases_dir:
        path = Path(d)
        datasets.append((path.name, load_test_cases(path)))
    for fpath in args.qa_file:
        path = Path(fpath)
        datasets.append((path.stem, load_qa_cases(path)))

    all_results = {
        "meta": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_sha": git_sha,
            "config": str(args.config),
            "flows": list(args.flow),
            "cases_dir": list(args.cases_dir),
            "qa_file": list(args.qa_file),
            "run_count": args.run_count,
            "run_start": args.run_start,
            "output_dir": args.output_dir,
            "experiment_id": args.experiment_id,
            "agent_system": args.agent_system,
        },
        "flows": {fn: {} for fn in args.flow},
    }

    output_dir = Path(args.output_dir) if args.output_dir else None
    command = shlex.join(sys.argv)
    hostname = socket.gethostname()
    now_iso = lambda: datetime.now(timezone.utc).isoformat()

    for flow_name in args.flow:
        flow_config = cfg.flows[flow_name]
        config_id = _compute_config_id(flow_name, flow_config)

        # Print flow config for debugging
        pprint.pprint(flow_config.model_dump())

        for dataset_name, cases in datasets:
            results = []
            latency_values: list[float] = []
            input_tokens_values: list[int] = []
            output_tokens_values: list[int] = []
            total_tokens_values: list[int] = []
            for case in cases:
                name = case["name"]
                desc = case["description"]
                files_dir = case.get("files_dir")
                input_data = build_input(desc, files_dir)
                for run_offset in range(args.run_count):
                    run_index = args.run_start + run_offset
                    started_at = now_iso()
                    execution_status = "success"
                    error_type = None
                    error_message = None
                    response = None
                    metrics_payload = {}
                    try:
                        result = await runner.execute(
                            flow_name=flow_name,
                            message=input_data,
                            session_id=f"eval_{flow_name}_{dataset_name}_{name}_{run_index}",
                            user_id="evaluator",
                            mode=ExecutionMode.SYNC,
                            interface="evaluation",
                        )
                        if result.success and result.output:
                            response = result.output.content
                            if not isinstance(response, str):
                                execution_status = "invalid_output"
                                error_type = "invalid_output_type"
                                error_message = (
                                    "Flow returned non-string output content"
                                )
                                response = str(response)
                            elif not response.strip():
                                execution_status = "invalid_output"
                                error_type = "empty_response"
                                error_message = (
                                    "Flow returned empty response content"
                                )
                        elif result.success and not result.output:
                            execution_status = "invalid_output"
                            error_type = "missing_output"
                            error_message = "Flow returned success without output content"
                        else:
                            execution_status = "execution_error"
                            error_type = "flow_execution_error"
                            error_message = str(result.error or "Unknown error")
                        metrics = ExecutionMetrics.from_output_metadata(result.metadata)
                        metrics_payload = metrics.to_metadata() if metrics else {}
                        if not metrics_payload and isinstance(result.metadata, dict):
                            latency = result.metadata.get("latency_ms")
                            if isinstance(latency, (int, float)):
                                metrics_payload = {"latency_ms": latency}
                    except Exception as e:
                        execution_status = _status_from_exception(e)
                        error_type = e.__class__.__name__
                        error_message = str(e)
                    finished_at = now_iso()

                    if isinstance(metrics_payload, dict):
                        latency = metrics_payload.get("latency_ms")
                        if isinstance(latency, (int, float)):
                            latency_values.append(float(latency))
                        token_usage = metrics_payload.get("token_usage")
                        if isinstance(token_usage, dict):
                            input_tokens = token_usage.get("input_tokens")
                            output_tokens = token_usage.get("output_tokens")
                            if isinstance(input_tokens, int):
                                input_tokens_values.append(input_tokens)
                            if isinstance(output_tokens, int):
                                output_tokens_values.append(output_tokens)
                            if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                                total_tokens_values.append(input_tokens + output_tokens)

                    result_payload = {
                        "test_case": name,
                        "run_index": run_index,
                        "response": response if response is not None else f"Error executing flow: {error_message or 'Unknown error'}",
                        "metrics": metrics_payload,
                        "status": execution_status,
                        "error_type": error_type,
                        "error_message": error_message,
                    }
                    results.append(result_payload)

                    if output_dir:
                        run_dir = (
                            output_dir
                            / args.experiment_id
                            / args.agent_system
                            / config_id
                            / str(name)
                            / str(run_index)
                        )
                        run_path = run_dir / "run.json"
                        if run_path.exists() and not args.allow_overwrite_runs:
                            raise FileExistsError(
                                f"Canonical run file already exists: {run_path}. "
                                "Choose a new --run-start or pass --allow-overwrite-runs."
                            )
                        run_dir.mkdir(parents=True, exist_ok=True)
                        run_record = {
                            "schema_version": "athos.run.v1",
                            "run_id": str(uuid.uuid4()),
                            "experiment_id": args.experiment_id,
                            "dataset_id": dataset_name,
                            "dataset_version": None,
                            "case_id": str(name),
                            "run_index": run_index,
                            "agent_system": args.agent_system,
                            "agent_version": f"git:{git_sha}" if git_sha else None,
                            "config_id": config_id,
                            "config_ref": str(args.config),
                            "execution": {
                                "started_at_utc": started_at,
                                "finished_at_utc": finished_at,
                                "status": execution_status,
                                "error_type": error_type,
                                "error_message": error_message,
                            },
                            "request": {
                                "input_text": input_data,
                                "input_artifacts": [],
                            },
                            "response": {
                                "output_text": response,
                                "output_artifacts": [],
                            },
                            "metrics": metrics_payload if isinstance(metrics_payload, dict) else {},
                            "provenance": {
                                "runner": "evals/run_evaluations.py",
                                "command": command,
                                "hostname": hostname,
                                "git_sha": git_sha,
                                "env_fingerprint": None,
                            },
                        }
                        run_path.write_text(json.dumps(run_record, indent=2))

            print(f"\nEvaluation Results for {flow_name} on {dataset_name}:")
            for r in results:
                print(f"- {r['test_case']}: status={r['status']}")

            def _percentile(values: list[float], percentile: float) -> float | None:
                if not values:
                    return None
                ordered = sorted(values)
                index = int(round((percentile / 100) * (len(ordered) - 1)))
                return ordered[index]

            summary = {
                "avg_latency_ms": (sum(latency_values) / len(latency_values)) if latency_values else None,
                "p50_latency_ms": _percentile(latency_values, 50),
                "p90_latency_ms": _percentile(latency_values, 90),
                "total_input_tokens": sum(input_tokens_values) if input_tokens_values else 0,
                "total_output_tokens": sum(output_tokens_values) if output_tokens_values else 0,
                "total_tokens": sum(total_tokens_values) if total_tokens_values else 0,
                "avg_total_tokens": (sum(total_tokens_values) / len(total_tokens_values)) if total_tokens_values else None,
            }

            all_results["flows"][flow_name][dataset_name] = {
                "summary": summary,
                "cases": results,
            }

    try:
        await runner.cleanup()
    except Exception as e:  # pragma: no cover - cleanup errors ignored
        print(f"Warning: failed to cleanup flow runner: {e}")

    if args.output:
        Path(args.output).write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
