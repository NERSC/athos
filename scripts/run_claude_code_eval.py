#!/usr/bin/env python3
"""Run Claude Code headlessly on ATHOS eval cases and emit external-runs JSONL."""

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


DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": ["answer", "citations"],
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_utc_iso() -> str:
    return now_utc().replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _extract_answer_and_sidecar(result_text: str) -> tuple[str | None, dict[str, Any]]:
    stripped = result_text.strip()
    if not stripped:
        return None, {}
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped, {}
    if not isinstance(payload, dict):
        return stripped, {}
    answer = payload.get("answer")
    if isinstance(answer, str) and answer.strip():
        sidecar = {
            key: value for key, value in payload.items() if key not in {"answer"}
        }
        return answer.strip(), sidecar
    return stripped, {"parsed_result": payload}


def _build_prompt(
    *,
    dataset_id: str,
    case_id: str,
    case_input: str,
    bundle_root: Path,
) -> str:
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

Return JSON only with this schema:
{json.dumps(DEFAULT_SCHEMA, indent=2)}
"""


def _build_claude_command(
    *,
    prompt: str,
    schema_json: str,
    model: str | None,
    permission_mode: str,
    bundle_root: Path,
    disallowed_tools: list[str],
) -> list[str]:
    cmd = [
        "claude",
        "--print",
        "--output-format",
        "json",
        "--permission-mode",
        permission_mode,
        "--add-dir",
        str(bundle_root),
        "--json-schema",
        schema_json,
    ]
    for tool_name in disallowed_tools:
        cmd.extend(["--disallowedTools", tool_name])
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _build_metrics(result_payload: dict[str, Any]) -> dict[str, Any]:
    usage = result_payload.get("usage") if isinstance(result_payload.get("usage"), dict) else {}
    input_tokens = _coerce_int(usage.get("input_tokens")) or 0
    output_tokens = _coerce_int(usage.get("output_tokens")) or 0
    cache_creation_input_tokens = _coerce_int(usage.get("cache_creation_input_tokens")) or 0
    cache_read_input_tokens = _coerce_int(usage.get("cache_read_input_tokens")) or 0
    metrics: dict[str, Any] = {
        "latency_ms": _coerce_int(result_payload.get("duration_ms")),
        "latency_api_ms": _coerce_int(result_payload.get("duration_api_ms")),
        "cost_usd": result_payload.get("total_cost_usd"),
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_creation_input_tokens": cache_creation_input_tokens,
            "cache_read_input_tokens": cache_read_input_tokens,
            "total_tokens": (
                input_tokens
                + output_tokens
                + cache_creation_input_tokens
                + cache_read_input_tokens
            ),
        },
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
    result_payload: dict[str, Any],
    stdout_text: str,
    git_sha: str | None,
) -> dict[str, Any]:
    result_text = result_payload.get("result")
    answer, sidecar = _extract_answer_and_sidecar(result_text if isinstance(result_text, str) else "")
    response_output = answer or (result_text if isinstance(result_text, str) else "")
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
        "response": {"output_text": response_output},
        "execution": {
            "status": "success",
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "error_type": None,
            "error_message": None,
        },
        "metrics": _build_metrics(result_payload),
        "provenance": {
            "runner": "scripts/run_claude_code_eval.py",
            "command": " ".join(command[:-1] + ["<PROMPT>"]),
            "hostname": socket.gethostname(),
            "git_sha": git_sha,
            "session_id": result_payload.get("session_id"),
            "uuid": result_payload.get("uuid"),
            "model_usage": result_payload.get("modelUsage", {}),
            "permission_denials": result_payload.get("permission_denials", []),
            "result_sidecar": sidecar,
            "raw_stdout": stdout_text,
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
    stdout_text: str = "",
    stderr_text: str = "",
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
        "metrics": {},
        "provenance": {
            "runner": "scripts/run_claude_code_eval.py",
            "command": " ".join(command[:-1] + ["<PROMPT>"]),
            "hostname": socket.gethostname(),
            "git_sha": git_sha,
            "raw_stdout": stdout_text,
            "raw_stderr": stderr_text,
        },
    }


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


def _parse_csv_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-file", default="evals/simple_qa.jsonl")
    parser.add_argument("--cases-dir", default="evals/test_cases")
    parser.add_argument(
        "--output",
        default="results/external_runs/claude_code_fs_bundle_v1.jsonl",
    )
    parser.add_argument("--agent-system", default="claude_code")
    parser.add_argument("--agent-version", default="claude-sonnet")
    parser.add_argument("--config-id", default="claude_code_fs_bundle_v1")
    parser.add_argument(
        "--config-ref",
        default="docs/cug_paper/CLAUDE_CODE_EVAL_GUIDE.md",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--permission-mode",
        default="default",
        choices=["acceptEdits", "bypassPermissions", "default", "dontAsk", "plan"],
        help="Claude Code permission mode. Do not use bypassPermissions unless you explicitly intend it.",
    )
    parser.add_argument(
        "--disallowed-tools",
        default="WebFetch,WebSearch,AskUserQuestion",
        help=(
            "Comma-separated list of built-in Claude tools to deny. "
            "Default blocks web/tool-escalation paths for eval purity."
        ),
    )
    parser.add_argument(
        "--bundle-root",
        default="workspace/file_retrieval_corpus",
        help="Read-only retrieval corpus root used by the prompt.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Limit execution to one or more case ids.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned cases without invoking Claude Code.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    qa_file = Path(args.qa_file)
    cases_dir = Path(args.cases_dir)
    output_path = Path(args.output)
    bundle_root = Path(args.bundle_root).resolve()
    index_path = bundle_root / "INDEX.md"

    if not qa_file.exists():
        raise FileNotFoundError(f"QA file not found: {qa_file}")
    if not cases_dir.exists():
        raise FileNotFoundError(f"Cases dir not found: {cases_dir}")
    if not index_path.exists():
        raise FileNotFoundError(f"Bundle index not found: {index_path}")

    all_cases = _load_cases(qa_file, cases_dir)
    selected_case_ids = set(args.case_id)
    if selected_case_ids:
        all_cases = [case for case in all_cases if case["case_id"] in selected_case_ids]

    if not all_cases:
        raise ValueError("No cases selected")

    schema_json = json.dumps(DEFAULT_SCHEMA, separators=(",", ":"))
    git_sha = _read_git_sha(REPO_ROOT)
    disallowed_tools = _parse_csv_list(args.disallowed_tools)

    if args.dry_run:
        for case in all_cases:
            print(f"{case['dataset_id']}/{case['case_id']}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as handle:
        for case in all_cases:
            prompt = _build_prompt(
                dataset_id=case["dataset_id"],
                case_id=case["case_id"],
                case_input=case["case_input"],
                bundle_root=bundle_root,
            )
            command = _build_claude_command(
                prompt=prompt,
                schema_json=schema_json,
                model=args.model,
                permission_mode=args.permission_mode,
                bundle_root=bundle_root,
                disallowed_tools=disallowed_tools,
            )

            print(f"Running {case['dataset_id']}/{case['case_id']}...", file=sys.stderr)
            started_at = now_utc_iso()
            with tempfile.TemporaryDirectory(prefix="claude_code_eval_") as isolated_cwd:
                completed = subprocess.run(
                    command,
                    cwd=isolated_cwd,
                    capture_output=True,
                    text=True,
                )
            finished_at = now_utc_iso()

            stdout_text = completed.stdout.strip()
            stderr_text = completed.stderr.strip()

            if completed.returncode != 0:
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
                    error_type="CliError",
                    error_message=stderr_text or f"claude exited with code {completed.returncode}",
                    git_sha=git_sha,
                    stdout_text=stdout_text,
                    stderr_text=stderr_text,
                )
            else:
                try:
                    result_payload = json.loads(stdout_text)
                except json.JSONDecodeError as exc:
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
                        error_type="JsonParseError",
                        error_message=f"Failed to parse Claude JSON output: {exc}",
                        git_sha=git_sha,
                        stdout_text=stdout_text,
                        stderr_text=stderr_text,
                    )
                else:
                    success = (
                        isinstance(result_payload, dict)
                        and result_payload.get("type") == "result"
                        and result_payload.get("subtype") == "success"
                        and result_payload.get("is_error") is False
                    )
                    if success:
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
                            result_payload=result_payload,
                            stdout_text=stdout_text,
                            git_sha=git_sha,
                        )
                    else:
                        error_message = stderr_text or stdout_text or "Claude returned non-success result"
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
                            error_type="ClaudeResultError",
                            error_message=error_message,
                            git_sha=git_sha,
                            stdout_text=stdout_text,
                            stderr_text=stderr_text,
                        )

            handle.write(json.dumps(record) + "\n")
            handle.flush()

    print(f"Wrote external run records to {output_path}")


if __name__ == "__main__":
    main()
