from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

from athos.models.flow import FlowOutput


def _load_pipeline() -> type:
    module_path = (
        Path(__file__).resolve().parents[3]
        / "integrations"
        / "openwebui"
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


class _NonStreamingRunner:
    """Stub FlowRunner that yields a single non-streaming chunk."""

    def __init__(self, output: FlowOutput) -> None:
        self._output = output

    async def stream(
        self,
        *,
        flow_name: str,
        message: str,
        session_id: str,
        user_id: str,
        interface: str,
        metadata: Dict[str, Any],
    ) -> AsyncGenerator[FlowOutput, None]:
        yield self._output


def _load_payload(raw: str) -> dict:
    assert raw.startswith("data: ")
    payload = raw[len("data: ") :].strip()
    return json.loads(payload)


def test_non_streamable_flow_emits_final_chunk_with_stop() -> None:
    output = FlowOutput(
        content="final response",
        metadata={
            "final": True,
            "streaming": False,
            "usage": {"prompt_tokens": 3, "completion_tokens": 7, "total_tokens": 10},
        },
    )

    pipeline = Pipeline()
    pipeline._runner = _NonStreamingRunner(output)
    pipeline._initialized = True

    stream = pipeline._stream_flow(
        flow_name="test-flow",
        message="hello",
        session_id="session-1",
        user_id="user-1",
        metadata={"model_id": "test-flow"},
    )

    chunks = list(stream)

    assert chunks[-1] == "data: [DONE]\n\n"

    message_chunk = _load_payload(chunks[0])
    assert message_chunk["choices"][0]["delta"]["content"] == "final response"
    assert message_chunk["choices"][0]["finish_reason"] is None

    final_chunk = _load_payload(chunks[-2])
    assert final_chunk["choices"][0]["finish_reason"] == "stop"
    assert final_chunk["usage"] == output.metadata["usage"]
