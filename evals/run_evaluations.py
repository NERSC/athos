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
import sys
import uuid

from dotenv import load_dotenv

from athos import build_config
from athos.models.enums import ExecutionMode
from athos.models.metrics import ExecutionMetrics
from athos.runtime.runner import FlowRunner

from eval_io import build_input, load_qa_cases, load_test_cases
from run_records import build_run_record, canonical_run_dir, ensure_safe_path_segment, now_utc_iso


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unknown"


def _normalize_for_hash(value):
    if hasattr(value, "model_dump"):
        try:
            return _normalize_for_hash(value.model_dump(mode="json"))
        except TypeError:
            return _normalize_for_hash(value.model_dump())
    if isinstance(value, dict):
        return {str(k): _normalize_for_hash(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_for_hash(v) for v in value]
    if isinstance(value, set):
        normalized = [_normalize_for_hash(v) for v in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _compute_config_id(flow_name: str, flow_config, model_config) -> str:
    normalized_flow_config = _normalize_for_hash(flow_config)
    normalized_model_config = _normalize_for_hash(model_config)
    payload = json.dumps(
        {
            "flow_config": normalized_flow_config,
            "model_config": normalized_model_config,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    model_name = "unknown"
    if isinstance(normalized_flow_config, dict):
        model_name = _slug(str(normalized_flow_config.get("model", "unknown")))
    return f"{_slug(flow_name)}__{model_name}__{digest}"


def _status_from_exception(error: Exception) -> str:
    if isinstance(error, TimeoutError):
        return "timeout"
    error_name = error.__class__.__name__.lower()
    if "timeout" in error_name:
        return "timeout"
    return "execution_error"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _build_aggregate_input_artifact(args: argparse.Namespace) -> list[dict]:
    manifest_payload: dict = {}
    manifest_path: Path | None = None
    if args.aggregate_manifest:
        manifest_path = Path(args.aggregate_manifest)
        if not manifest_path.exists():
            raise FileNotFoundError(f"Aggregate manifest not found: {manifest_path}")
        manifest_payload = _load_json(manifest_path)

    aggregate_name = args.aggregate_name or manifest_payload.get("aggregate_name")
    aggregate_version = args.aggregate_version or manifest_payload.get("aggregate_version")
    aggregate_persist_dir = (
        args.aggregate_persist_dir or manifest_payload.get("output_persist_dir")
    )

    if not any([aggregate_name, aggregate_version, aggregate_persist_dir, manifest_path]):
        return []

    metadata = {
        "aggregate_name": aggregate_name,
        "aggregate_version": aggregate_version,
        "output_persist_dir": aggregate_persist_dir,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "manifest_created_utc": manifest_payload.get("created_utc"),
        "manifest_git_sha": manifest_payload.get("git_sha"),
        "manifest_script_version": manifest_payload.get("script_version"),
    }
    return [
        {
            "type": "chroma_aggregate_db",
            "display_name": (
                f"chroma_aggregate:{aggregate_name}@{aggregate_version}"
                if aggregate_name and aggregate_version
                else "chroma_aggregate_db"
            ),
            "path": aggregate_persist_dir,
            "metadata": metadata,
        }
    ]


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
        "--output-dir",
        required=True,
        help="Output directory for canonical per-run run.json artifacts",
    )
    parser.add_argument(
        "--experiment-id",
        required=True,
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
    parser.add_argument(
        "--aggregate-manifest",
        default=None,
        help=(
            "Optional path to aggregate Chroma manifest JSON. "
            "If provided, aggregate metadata is stored in request.input_artifacts."
        ),
    )
    parser.add_argument(
        "--aggregate-name",
        default=None,
        help="Optional aggregate DB logical name to record in run artifacts",
    )
    parser.add_argument(
        "--aggregate-version",
        default=None,
        help="Optional aggregate DB version to record in run artifacts",
    )
    parser.add_argument(
        "--aggregate-persist-dir",
        default=None,
        help="Optional aggregate DB persist_dir to record in run artifacts",
    )
    args = parser.parse_args()
    load_dotenv()

    if args.run_count < 1:
        raise ValueError("--run-count must be >= 1")
    if args.run_start < 0:
        raise ValueError("--run-start must be >= 0")
    ensure_safe_path_segment(args.agent_system, "agent_system")
    ensure_safe_path_segment(args.experiment_id, "experiment_id")

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
    try:
        print("Loaded flows:")
        print(args.flow)

        datasets = []
        for d in args.cases_dir:
            path = Path(d)
            datasets.append((path.name, load_test_cases(path)))
        for fpath in args.qa_file:
            path = Path(fpath)
            datasets.append((path.stem, load_qa_cases(path)))

        output_dir = Path(args.output_dir)
        command = shlex.join(sys.argv)
        hostname = socket.gethostname()
        aggregate_input_artifacts = _build_aggregate_input_artifact(args)

        planned_runs = []
        target_path_counts: dict[Path, int] = {}
        for flow_name in args.flow:
            flow_config = cfg.flows[flow_name]
            model_alias = getattr(flow_config, "model", None)
            model_config = cfg.models.get(model_alias) if model_alias else None
            config_id = _compute_config_id(flow_name, flow_config, model_config)

            # Print flow config for debugging
            pprint.pprint(flow_config.model_dump())

            for dataset_name, cases in datasets:
                safe_dataset_id = ensure_safe_path_segment(str(dataset_name), "dataset_id")
                for case in cases:
                    name = case["name"]
                    desc = case["description"]
                    files_dir = case.get("files_dir")
                    input_data = build_input(desc, files_dir)
                    safe_case_id = ensure_safe_path_segment(str(name), "case_id")
                    for run_offset in range(args.run_count):
                        run_index = args.run_start + run_offset
                        run_dir = canonical_run_dir(
                            output_root=output_dir,
                            experiment_id=args.experiment_id,
                            agent_system=args.agent_system,
                            config_id=config_id,
                            dataset_id=safe_dataset_id,
                            case_id=safe_case_id,
                            run_index=run_index,
                        )
                        run_path = run_dir / "run.json"
                        planned_runs.append(
                            {
                                "flow_name": flow_name,
                                "dataset_name": dataset_name,
                                "case_name": name,
                                "input_data": input_data,
                                "run_index": run_index,
                                "run_dir": run_dir,
                                "run_path": run_path,
                                "config_id": config_id,
                                "safe_dataset_id": safe_dataset_id,
                                "safe_case_id": safe_case_id,
                            }
                        )
                        target_path_counts[run_path] = target_path_counts.get(run_path, 0) + 1

        if not args.allow_overwrite_runs:
            duplicate_targets = sorted(
                str(path) for path, count in target_path_counts.items() if count > 1
            )
            if duplicate_targets:
                raise FileExistsError(
                    "Duplicate canonical run targets detected before execution: "
                    f"{', '.join(duplicate_targets[:3])}. "
                    "Resolve colliding case identifiers or choose a different run index range."
                )

            existing_targets = sorted(
                str(path) for path in target_path_counts if path.exists()
            )
            if existing_targets:
                raise FileExistsError(
                    "Canonical run file already exists: "
                    f"{existing_targets[0]}. "
                    "Choose a new --run-start or pass --allow-overwrite-runs."
                )

        total_runs = 0
        for planned in planned_runs:
            started_at = now_utc_iso()
            execution_status = "success"
            error_type = None
            error_message = None
            response = None
            metrics_payload = {}
            try:
                result = await runner.execute(
                    flow_name=planned["flow_name"],
                    message=planned["input_data"],
                    session_id=(
                        f"eval_{planned['flow_name']}_{planned['dataset_name']}_"
                        f"{planned['case_name']}_{planned['run_index']}"
                    ),
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
            finished_at = now_utc_iso()
            planned["run_dir"].mkdir(parents=True, exist_ok=True)
            run_record = build_run_record(
                run_id=str(uuid.uuid4()),
                experiment_id=args.experiment_id,
                dataset_id=planned["safe_dataset_id"],
                dataset_version=None,
                case_id=planned["safe_case_id"],
                run_index=planned["run_index"],
                agent_system=args.agent_system,
                agent_version=f"git:{git_sha}" if git_sha else None,
                config_id=planned["config_id"],
                config_ref=str(args.config),
                execution={
                    "started_at_utc": started_at,
                    "finished_at_utc": finished_at,
                    "status": execution_status,
                    "error_type": error_type,
                    "error_message": error_message,
                },
                request={
                    "input_text": planned["input_data"],
                    "input_artifacts": aggregate_input_artifacts,
                },
                response={"output_text": response, "output_artifacts": []},
                metrics=metrics_payload if isinstance(metrics_payload, dict) else {},
                provenance={
                    "runner": "evals/run_evaluations.py",
                    "command": command,
                    "hostname": hostname,
                    "git_sha": git_sha,
                    "env_fingerprint": None,
                },
            )
            planned["run_path"].write_text(json.dumps(run_record, indent=2))
            total_runs += 1

        print(f"Wrote {total_runs} canonical runs under {output_dir / args.experiment_id}")
    finally:
        try:
            await runner.cleanup()
        except Exception as e:  # pragma: no cover - cleanup errors ignored
            print(f"Warning: failed to cleanup flow runner: {e}")


if __name__ == "__main__":
    asyncio.run(main())
