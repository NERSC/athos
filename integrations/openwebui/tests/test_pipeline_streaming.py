"""Tests for the ATHOS FlowRunner OpenWebUI pipeline streaming helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_pipeline() -> type:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "pipelines"
        / "athos_flowrunner_manifold_pipeline.py"
    )
    spec = importlib.util.spec_from_file_location(
        "athos_flowrunner_manifold_pipeline", module_path
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Failed to load pipeline module spec")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Pipeline


Pipeline = _load_pipeline()


def _load_payload(raw: str) -> dict:
    assert raw.startswith("data: ")
    payload = raw[len("data: ") :].strip()
    return json.loads(payload)


def test_build_stream_final_includes_metadata() -> None:
    pipeline = Pipeline()
    metadata = {
        "model": "gpt-4o-mini",
        "tool_calls": [{"id": "tool_1", "type": "function"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    raw = pipeline._build_stream_final("chunk-1", 123, "default-model", "", metadata=metadata)
    data = _load_payload(raw)

    assert data["model"] == "gpt-4o-mini"
    assert data["usage"] == metadata["usage"]

    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["delta"]["content"] == ""
    assert choice["delta"]["tool_calls"] == metadata["tool_calls"]


def test_build_stream_final_without_metadata_defaults() -> None:
    pipeline = Pipeline()

    raw = pipeline._build_stream_final("chunk-1", 123, "default-model", "final message")
    data = _load_payload(raw)

    assert data["model"] == "default-model"
    assert "usage" not in data

    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["delta"]["content"] == "final message"
    assert "tool_calls" not in choice["delta"]
