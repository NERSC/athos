"""Tool wrapper for athos_qa/generate_qa_dataset.py."""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from smolagents import tool


def _repo_root() -> Path:
    """Return repository root path."""
    return Path(__file__).resolve().parents[3]


def _script_path() -> Path:
    """Return path to the QA dataset generation script."""
    return _repo_root() / "athos_qa" / "generate_qa_dataset.py"


def _build_command(
    *,
    input_dir: str | None,
    input_file: str | None,
    url: str | None,
    validate: str | None,
    output: str,
    max_chunks: int | None,
    backend: str,
    model: str | None,
) -> list[str]:
    """Build command-line arguments for generate_qa_dataset.py."""
    script = _script_path()
    cmd = [sys.executable, str(script)]

    sources = [bool(input_dir), bool(input_file), bool(url)]
    if validate and any(sources):
        raise ValueError("Do not set --validate with --input-dir/--input-file/--url.")
    if sum(sources) > 1:
        raise ValueError("Provide only one source: input_dir, input_file, or url.")

    if validate:
        cmd.extend(["--validate", validate])
        return cmd

    if input_dir:
        cmd.extend(["--input-dir", input_dir])
    elif input_file:
        cmd.extend(["--input-file", input_file])
    elif url:
        cmd.extend(["--url", url])
    else:
        cmd.extend(["--input-dir", "docs"])

    cmd.extend(["--output", output, "--backend", backend])

    if max_chunks is not None:
        if max_chunks <= 0:
            raise ValueError("max_chunks must be > 0 when provided.")
        cmd.extend(["--max-chunks", str(max_chunks)])

    if model:
        cmd.extend(["--model", model])

    return cmd


@tool
def generate_qa_dataset_tool(
    input_dir: str | None = None,
    input_file: str | None = None,
    url: str | None = None,
    output: str = "athos_qa/generated_qa_dataset.jsonl",
    max_chunks: int | None = None,
    backend: str = "auto",
    model: str | None = None,
    validate: str | None = None,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    """Run ATHOS Q&A dataset generation from local docs, a file, or a URL.

    Args:
        input_dir: Directory of .md/.txt/.rst files. If omitted and no other source is set, defaults to `docs`.
        input_file: Single markdown/text file to process.
        url: URL to fetch and process.
        output: Output JSONL path for raw generated pairs.
        max_chunks: Optional chunk limit for quick test runs.
        backend: LLM backend: auto, cborg, anthropic, or openai.
        model: Optional model override for the chosen backend.
        validate: Validate an existing dataset path instead of generating a new one.
        timeout_seconds: Max runtime for the subprocess command.

    Returns:
        Structured result with status, command, exit code, logs, and output paths.
    """
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be > 0.")

    script = _script_path()
    if not script.exists():
        raise FileNotFoundError(f"Could not find script at {script}")

    cmd = _build_command(
        input_dir=input_dir,
        input_file=input_file,
        url=url,
        validate=validate,
        output=output,
        max_chunks=max_chunks,
        backend=backend,
        model=model,
    )

    run_result = subprocess.run(
        cmd,
        cwd=str(_repo_root()),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    stdout = (run_result.stdout or "").strip()
    stderr = (run_result.stderr or "").strip()
    response: dict[str, Any] = {
        "status": "success" if run_result.returncode == 0 else "error",
        "exit_code": run_result.returncode,
        "command": shlex.join(cmd),
        "stdout_tail": "\n".join(stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(stderr.splitlines()[-20:]),
    }

    if validate:
        return response

    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = _repo_root() / output_path
    deduped_path = output_path.with_suffix(".deduped.jsonl")

    response["output_path"] = str(output_path)
    response["deduped_output_path"] = str(deduped_path)
    return response
