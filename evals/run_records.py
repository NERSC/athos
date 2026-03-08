"""Shared helpers for canonical ATHOS run records."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_safe_path_segment(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing required non-empty string field: {field}")
    p = Path(value)
    if p.is_absolute():
        raise ValueError(f"Field '{field}' must be a relative path segment")
    if value in {".", ".."}:
        raise ValueError(f"Field '{field}' contains an invalid path segment")
    parts = p.parts
    if len(parts) != 1 or parts[0] in {".", ".."}:
        raise ValueError(f"Field '{field}' must not contain path separators or traversal")
    if "\\" in value:
        raise ValueError(f"Field '{field}' must not contain path separators")
    return value


def canonical_run_dir(
    *,
    output_root: str | Path,
    experiment_id: str,
    agent_system: str,
    config_id: str,
    dataset_id: str,
    case_id: str,
    run_index: int,
) -> Path:
    safe_experiment_id = ensure_safe_path_segment(experiment_id, "experiment_id")
    safe_agent_system = ensure_safe_path_segment(agent_system, "agent_system")
    safe_config_id = ensure_safe_path_segment(config_id, "config_id")
    safe_dataset_id = ensure_safe_path_segment(dataset_id, "dataset_id")
    safe_case_id = ensure_safe_path_segment(case_id, "case_id")
    return (
        Path(output_root)
        / safe_experiment_id
        / safe_agent_system
        / safe_config_id
        / safe_dataset_id
        / safe_case_id
        / str(run_index)
    )


def build_run_record(
    *,
    run_id: str,
    experiment_id: str,
    dataset_id: str,
    dataset_version: str | None,
    case_id: str,
    run_index: int,
    agent_system: str,
    agent_version: str | None,
    config_id: str,
    config_ref: str | None,
    execution: dict[str, Any],
    request: dict[str, Any],
    response: dict[str, Any],
    metrics: dict[str, Any] | None,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    started_at = execution.get("started_at_utc")
    finished_at = execution.get("finished_at_utc")
    return {
        "schema_version": "athos.run.v1",
        "run_id": run_id,
        "experiment_id": experiment_id,
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "case_id": case_id,
        "run_index": run_index,
        "agent_system": agent_system,
        "agent_version": agent_version,
        "config_id": config_id,
        "config_ref": config_ref,
        "execution": {
            "started_at_utc": started_at if isinstance(started_at, str) else now_utc_iso(),
            "finished_at_utc": finished_at if isinstance(finished_at, str) else now_utc_iso(),
            "status": execution.get("status", "success"),
            "error_type": execution.get("error_type"),
            "error_message": execution.get("error_message"),
            "failure_class": execution.get("failure_class"),
            "retryable": execution.get("retryable"),
        },
        "request": {
            "input_text": request.get("input_text"),
            "input_artifacts": request.get("input_artifacts", []),
        },
        "response": {
            "output_text": response.get("output_text"),
            "output_artifacts": response.get("output_artifacts", []),
        },
        "metrics": metrics if isinstance(metrics, dict) else {},
        "provenance": {
            "runner": provenance.get("runner"),
            "command": provenance.get("command"),
            "hostname": provenance.get("hostname"),
            "git_sha": provenance.get("git_sha"),
            "env_fingerprint": provenance.get("env_fingerprint"),
        },
    }
