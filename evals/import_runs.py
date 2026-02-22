#!/usr/bin/env python3
"""Import external run outputs into canonical ATHOS run.json layout."""

from __future__ import annotations

import argparse
import json
import socket
import uuid
from pathlib import Path
from typing import Any

from run_records import build_run_record, canonical_run_dir, ensure_safe_path_segment


def _read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        items = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                items.append(json.loads(line))
        return items

    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("Import payload must be JSON object, JSON array, or JSONL")


def _validate_record(record: dict[str, Any]) -> None:
    ensure_safe_path_segment(record.get("case_id"), "case_id")
    ensure_safe_path_segment(record.get("agent_system"), "agent_system")
    ensure_safe_path_segment(record.get("config_id"), "config_id")
    dataset_id = record.get("dataset_id")
    if isinstance(dataset_id, str) and dataset_id:
        ensure_safe_path_segment(dataset_id, "dataset_id")

    execution = record.get("execution")
    status = "success"
    if isinstance(execution, dict):
        status_value = execution.get("status")
        if isinstance(status_value, str) and status_value:
            status = status_value

    response_payload = record.get("response")
    output_text = None
    if isinstance(response_payload, dict):
        output_text = response_payload.get("output_text")
    if output_text is None and isinstance(record.get("output_text"), str):
        output_text = record["output_text"]

    if status == "success" and not (isinstance(output_text, str) and output_text.strip()):
        raise ValueError(
            "Record with success status must include response.output_text (or top-level output_text)"
        )

    if status != "success":
        error_type = None
        error_message = None
        if isinstance(execution, dict):
            error_type = execution.get("error_type")
            error_message = execution.get("error_message")
        if not isinstance(error_type, str) and not isinstance(error_message, str):
            raise ValueError(
                "Non-success records must include execution.error_type or execution.error_message"
            )


def _to_run_record(
    record: dict[str, Any],
    experiment_id: str,
    dataset_id: str | None,
    dataset_version: str | None,
    config_ref: str | None,
    command: str,
) -> dict[str, Any]:
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    response_payload = record.get("response") if isinstance(record.get("response"), dict) else {}
    request_payload = record.get("request") if isinstance(record.get("request"), dict) else {}
    metrics_payload = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
    provenance_payload = record.get("provenance") if isinstance(record.get("provenance"), dict) else {}

    output_text = response_payload.get("output_text")
    if output_text is None and isinstance(record.get("output_text"), str):
        output_text = record["output_text"]

    status = execution.get("status")
    if not isinstance(status, str) or not status:
        status = "success"

    resolved_dataset_id = (
        record.get("dataset_id")
        if isinstance(record.get("dataset_id"), str) and record.get("dataset_id")
        else dataset_id
    )
    if not isinstance(resolved_dataset_id, str) or not resolved_dataset_id:
        raise ValueError("Imported record is missing dataset_id")
    input_run_id = record.get("run_id")
    run_id = input_run_id if isinstance(input_run_id, str) and input_run_id else str(uuid.uuid4())

    return build_run_record(
        run_id=run_id,
        experiment_id=experiment_id,
        dataset_id=resolved_dataset_id,
        dataset_version=(
            record.get("dataset_version")
            if isinstance(record.get("dataset_version"), str)
            else dataset_version
        ),
        case_id=record["case_id"],
        run_index=int(record.get("run_index", 0)),
        agent_system=record["agent_system"],
        agent_version=record.get("agent_version"),
        config_id=record["config_id"],
        config_ref=(
            record.get("config_ref")
            if isinstance(record.get("config_ref"), str) and record.get("config_ref")
            else config_ref
        ),
        execution={
            "started_at_utc": execution.get("started_at_utc"),
            "finished_at_utc": execution.get("finished_at_utc"),
            "status": status,
            "error_type": execution.get("error_type"),
            "error_message": execution.get("error_message"),
        },
        request={
            "input_text": request_payload.get("input_text"),
            "input_artifacts": request_payload.get("input_artifacts", []),
        },
        response={
            "output_text": output_text,
            "output_artifacts": response_payload.get("output_artifacts", []),
        },
        metrics=metrics_payload,
        provenance={
            "runner": provenance_payload.get("runner", "evals/import_runs.py"),
            "command": provenance_payload.get("command", command),
            "hostname": provenance_payload.get("hostname", socket.gethostname()),
            "git_sha": provenance_payload.get("git_sha"),
            "env_fingerprint": provenance_payload.get("env_fingerprint"),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSONL/JSON containing external runs")
    parser.add_argument("--output-dir", required=True, help="Canonical output root")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--dataset-id", default=None)
    parser.add_argument("--dataset-version", default=None)
    parser.add_argument("--config-ref", default=None)
    parser.add_argument(
        "--allow-overwrite-runs",
        action="store_true",
        help="Allow overwriting existing canonical run.json artifacts",
    )
    args = parser.parse_args()
    ensure_safe_path_segment(args.experiment_id, "experiment_id")
    if args.dataset_id:
        ensure_safe_path_segment(args.dataset_id, "dataset_id")

    input_path = Path(args.input)
    records = _read_records(input_path)
    if not records:
        raise ValueError("No import records found")

    written = 0
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record at index {idx} is not a JSON object")
        _validate_record(record)
        run_record = _to_run_record(
            record=record,
            experiment_id=args.experiment_id,
            dataset_id=args.dataset_id,
            dataset_version=args.dataset_version,
            config_ref=args.config_ref,
            command=" ".join(["python", "evals/import_runs.py", "--input", str(input_path)]),
        )

        dataset_value = run_record.get("dataset_id")
        if not isinstance(dataset_value, str) or not dataset_value:
            raise ValueError(
                f"Record at index {idx} does not define dataset_id and no --dataset-id was provided"
            )
        run_dir = canonical_run_dir(
            output_root=args.output_dir,
            experiment_id=args.experiment_id,
            agent_system=str(run_record["agent_system"]),
            config_id=str(run_record["config_id"]),
            dataset_id=str(run_record["dataset_id"]),
            case_id=str(run_record["case_id"]),
            run_index=int(run_record["run_index"]),
        )
        run_path = run_dir / "run.json"
        if run_path.exists() and not args.allow_overwrite_runs:
            raise FileExistsError(
                f"Canonical run file already exists: {run_path}. "
                "Pass --allow-overwrite-runs to overwrite."
            )
        run_dir.mkdir(parents=True, exist_ok=True)
        run_path.write_text(json.dumps(run_record, indent=2))
        written += 1

    print(f"Wrote {written} canonical runs under {args.output_dir}/{args.experiment_id}")


if __name__ == "__main__":
    main()
