#!/usr/bin/env python3
"""Run Codex headlessly on ATHOS eval cases and emit external-runs JSONL."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import socket
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_IO_PATH = REPO_ROOT / "evals" / "eval_io.py"

spec = importlib.util.spec_from_file_location("eval_io_mod", EVAL_IO_PATH)
eval_io_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(eval_io_mod)

load_qa_cases = eval_io_mod.load_qa_cases
load_test_cases = eval_io_mod.load_test_cases
build_input = eval_io_mod.build_input


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_utc_iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_git_sha(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    sha = completed.stdout.strip()
    return sha or None


def _build_prompt(*, dataset_id: str, case_id: str, case_input: str, bundle_root: Path) -> str:
    return f"""You are running a single ATHOS paper benchmark case as a standalone coding agent baseline.

Rules:
- Do not inspect any `solution.md` file.
- Do not modify repository files.
- Use read-only tool usage only.
- Treat `{bundle_root}` as your primary evidence source.
- Read `{bundle_root}/INDEX.md` before broader searching.
- Prefer targeted reads over repeated broad searches.
- Keep the final support answer concise and operationally useful.

Case metadata:
- dataset_id: {dataset_id}
- case_id: {case_id}

User-facing case input:
{case_input}
"""


def _build_codex_command(
    *,
    prompt: str,
    bundle_root: Path,
    output_last_message: Path,
    sandbox_mode: str,
    enable_web_search: bool,
    model: str | None,
) -> list[str]:
    cmd = [
        "codex",
        "exec",
        "--json",
        "--sandbox",
        sandbox_mode,
        "--skip-git-repo-check",
        "--ephemeral",
        "--add-dir",
        str(bundle_root),
        "--output-last-message",
        str(output_last_message),
    ]
    if enable_web_search:
        cmd.append("--search")
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def _load_cases(qa_file: Path, cases_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in load_qa_cases(qa_file):
        rows.append(
            {
                "dataset_id": qa_file.stem,
                "case_id": case["name"],
                "case_input": case["description"],
            }
        )
    for case in load_test_cases(cases_dir):
        rows.append(
            {
                "dataset_id": cases_dir.name,
                "case_id": case["name"],
                "case_input": build_input(case["description"], case.get("files_dir")),
            }
        )
    return rows


def _parse_codex_json_events(raw_stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in raw_stdout.splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _extract_usage_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    usage_payload: dict[str, Any] = {}
    for event in events:
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
            if isinstance(usage, dict):
                usage_payload = usage
    return usage_payload


def _build_metrics(
    *,
    started_at: datetime,
    finished_at: datetime,
    usage_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    latency_ms = int((finished_at - started_at).total_seconds() * 1000)
    metrics: dict[str, Any] = {"latency_ms": latency_ms}
    if not isinstance(usage_payload, dict):
        return metrics

    input_tokens = usage_payload.get("input_tokens")
    output_tokens = usage_payload.get("output_tokens")
    cached_input_tokens = usage_payload.get("cached_input_tokens")
    if not isinstance(input_tokens, int):
        input_tokens = 0
    if not isinstance(output_tokens, int):
        output_tokens = 0
    if not isinstance(cached_input_tokens, int):
        cached_input_tokens = 0
    metrics["token_usage"] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_input_tokens,
        "total_tokens": input_tokens + output_tokens + cached_input_tokens,
    }
    return metrics


def _build_success_record(
    *,
    dataset_id: str,
    case_id: str,
    run_index: int,
    agent_system: str,
    agent_version: str,
    config_id: str,
    config_ref: str,
    prompt: str,
    command: list[str],
    started_at_utc: str,
    finished_at_utc: str,
    output_text: str,
    git_sha: str | None,
    raw_stdout: str,
    raw_stderr: str,
    metrics: dict[str, Any],
    event_count: int,
) -> dict[str, Any]:
    return {
        "run_id": str(uuid.uuid4()),
        "dataset_id": dataset_id,
        "case_id": case_id,
        "run_index": run_index,
        "agent_system": agent_system,
        "agent_version": agent_version,
        "config_id": config_id,
        "config_ref": config_ref,
        "request": {"input_text": prompt},
        "response": {"output_text": output_text},
        "execution": {
            "status": "success",
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "error_type": None,
            "error_message": None,
        },
        "metrics": metrics,
        "provenance": {
            "runner": "scripts/run_codex_eval.py",
            "command": " ".join(command[:-1] + ["<PROMPT>"]),
            "hostname": socket.gethostname(),
            "git_sha": git_sha,
            "codex_event_count": event_count,
            "raw_stdout": raw_stdout,
            "raw_stderr": raw_stderr,
        },
    }


def _build_error_record(
    *,
    dataset_id: str,
    case_id: str,
    run_index: int,
    agent_system: str,
    agent_version: str,
    config_id: str,
    config_ref: str,
    prompt: str,
    command: list[str],
    started_at_utc: str,
    finished_at_utc: str,
    error_type: str,
    error_message: str,
    git_sha: str | None,
    raw_stdout: str,
    raw_stderr: str,
    metrics: dict[str, Any],
    event_count: int,
) -> dict[str, Any]:
    return {
        "run_id": str(uuid.uuid4()),
        "dataset_id": dataset_id,
        "case_id": case_id,
        "run_index": run_index,
        "agent_system": agent_system,
        "agent_version": agent_version,
        "config_id": config_id,
        "config_ref": config_ref,
        "request": {"input_text": prompt},
        "response": {"output_text": None},
        "execution": {
            "status": "execution_error",
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "error_type": error_type,
            "error_message": error_message,
        },
        "metrics": metrics,
        "provenance": {
            "runner": "scripts/run_codex_eval.py",
            "command": " ".join(command[:-1] + ["<PROMPT>"]),
            "hostname": socket.gethostname(),
            "git_sha": git_sha,
            "codex_event_count": event_count,
            "raw_stdout": raw_stdout,
            "raw_stderr": raw_stderr,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-file", default="evals/simple_qa.jsonl")
    parser.add_argument("--cases-dir", default="evals/test_cases")
    parser.add_argument("--bundle-root", default="workspace/file_retrieval_corpus")
    parser.add_argument("--output", default="results/external_runs/codex_fs_bundle_v1.jsonl")
    parser.add_argument("--agent-system", default="codex")
    parser.add_argument("--agent-version", default="gpt-5-codex")
    parser.add_argument("--config-id", default="codex_fs_bundle_v1")
    parser.add_argument("--config-ref", default="scripts/run_codex_eval.py")
    parser.add_argument("--model", default=None)
    parser.add_argument("--sandbox-mode", default="workspace-write")
    parser.add_argument("--enable-web-search", action="store_true")
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    qa_file = Path(args.qa_file)
    cases_dir = Path(args.cases_dir)
    bundle_root = Path(args.bundle_root).resolve()
    output_path = Path(args.output)

    if not qa_file.exists():
        raise FileNotFoundError(f"QA file not found: {qa_file}")
    if not cases_dir.exists():
        raise FileNotFoundError(f"Cases dir not found: {cases_dir}")
    if not (bundle_root / "INDEX.md").exists():
        raise FileNotFoundError(f"Bundle index not found: {bundle_root / 'INDEX.md'}")

    all_cases = _load_cases(qa_file, cases_dir)
    selected_case_ids = set(args.case_id)
    if selected_case_ids:
        all_cases = [case for case in all_cases if case["case_id"] in selected_case_ids]
    if not all_cases:
        raise ValueError("No cases selected")

    if args.dry_run:
        for case in all_cases:
            print(f"{case['dataset_id']}/{case['case_id']}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    git_sha = _read_git_sha(REPO_ROOT)

    with output_path.open("a", encoding="utf-8") as handle:
        for case in all_cases:
            prompt = _build_prompt(
                dataset_id=case["dataset_id"],
                case_id=case["case_id"],
                case_input=case["case_input"],
                bundle_root=bundle_root,
            )
            with tempfile.TemporaryDirectory(prefix="codex_eval_") as isolated_cwd:
                output_last_message = Path(isolated_cwd) / "codex_last_message.txt"
                command = _build_codex_command(
                    prompt=prompt,
                    bundle_root=bundle_root,
                    output_last_message=output_last_message,
                    sandbox_mode=args.sandbox_mode,
                    enable_web_search=args.enable_web_search,
                    model=args.model,
                )
                print(f"Running {case['dataset_id']}/{case['case_id']}...", file=sys.stderr)
                started_at_dt = datetime.now(timezone.utc)
                completed = subprocess.run(
                    command,
                    cwd=isolated_cwd,
                    capture_output=True,
                    text=True,
                )
                finished_at_dt = datetime.now(timezone.utc)
                started_at = _to_utc_iso(started_at_dt)
                finished_at = _to_utc_iso(finished_at_dt)

                raw_stdout = completed.stdout.strip()
                raw_stderr = completed.stderr.strip()
                events = _parse_codex_json_events(raw_stdout)
                usage_payload = _extract_usage_from_events(events)
                metrics = _build_metrics(
                    started_at=started_at_dt,
                    finished_at=finished_at_dt,
                    usage_payload=usage_payload,
                )
                output_text = (
                    output_last_message.read_text(encoding="utf-8").strip()
                    if output_last_message.exists()
                    else ""
                )

                if completed.returncode == 0 and output_text:
                    record = _build_success_record(
                        dataset_id=case["dataset_id"],
                        case_id=case["case_id"],
                        run_index=0,
                        agent_system=args.agent_system,
                        agent_version=args.agent_version,
                        config_id=args.config_id,
                        config_ref=args.config_ref,
                        prompt=prompt,
                        command=command,
                        started_at_utc=started_at,
                        finished_at_utc=finished_at,
                        output_text=output_text,
                        git_sha=git_sha,
                        raw_stdout=raw_stdout,
                        raw_stderr=raw_stderr,
                        metrics=metrics,
                        event_count=len(events),
                    )
                else:
                    error_message = raw_stderr or raw_stdout or f"codex exited with code {completed.returncode}"
                    record = _build_error_record(
                        dataset_id=case["dataset_id"],
                        case_id=case["case_id"],
                        run_index=0,
                        agent_system=args.agent_system,
                        agent_version=args.agent_version,
                        config_id=args.config_id,
                        config_ref=args.config_ref,
                        prompt=prompt,
                        command=command,
                        started_at_utc=started_at,
                        finished_at_utc=finished_at,
                        error_type="CodexExecError",
                        error_message=error_message,
                        git_sha=git_sha,
                        raw_stdout=raw_stdout,
                        raw_stderr=raw_stderr,
                        metrics=metrics,
                        event_count=len(events),
                    )

                handle.write(json.dumps(record) + "\n")
                handle.flush()

    print(f"Wrote external run records to {output_path}")


if __name__ == "__main__":
    main()
