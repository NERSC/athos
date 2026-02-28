from __future__ import annotations

import subprocess
import pytest

from athos.tools.qa_dataset import _build_command, generate_qa_dataset_tool


def test_build_command_rejects_multiple_sources():
    with pytest.raises(ValueError, match="Provide only one source"):
        _build_command(
            input_dir="docs",
            input_file="doc.md",
            url=None,
            validate=None,
            output="out.jsonl",
            max_chunks=None,
            backend="auto",
            model=None,
        )


def test_generate_tool_returns_output_paths(monkeypatch, tmp_path):
    repo = tmp_path
    script = repo / "athos_qa" / "generate_qa_dataset.py"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    monkeypatch.setattr("athos.tools.qa_dataset._repo_root", lambda: repo)
    monkeypatch.setattr("athos.tools.qa_dataset._script_path", lambda: script)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=kwargs.get("args", args[0] if args else []),
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr("athos.tools.qa_dataset.subprocess.run", fake_run)

    result = generate_qa_dataset_tool(
        input_dir="docs",
        output="athos_qa/generated.jsonl",
    )

    assert result["status"] == "success"
    assert result["output_path"] == str(repo / "athos_qa" / "generated.jsonl")
    assert result["deduped_output_path"] == str(repo / "athos_qa" / "generated.deduped.jsonl")
