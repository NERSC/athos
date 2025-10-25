"""Athos hello-world manifold pipeline for OpenWebUI Pipelines.

This pipeline demonstrates how Athos can expose multiple logical
"models" from a single pipeline implementation without invoking any
Athos flows yet.  It returns deterministic responses that highlight how
per-model behavior can be implemented ahead of deeper runtime
integration.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Generator, Iterable, Iterator, List, Union

from pydantic import BaseModel


class Pipeline:
    """Minimal manifold pipeline that simulates two Athos models."""

    class Valves(BaseModel):
        """Runtime configuration presented in the OpenWebUI admin panel."""

        greeting_prefix: str = "Hello"
        include_timestamp: bool = True

    def __init__(self) -> None:
        self.type = "manifold"
        self.name = "Athos Hello World"
        self.version = "0.1.0"
        self.description = (
            "Demonstrates a simple manifold pipeline with two mock Athos"
            " personalities."
        )
        self.author = "Athos Team"

        self.valves = self.Valves()

        # Pipelines surface multiple "models" to OpenWebUI. The identifiers
        # below become selectable options inside the UI.
        self.pipelines = [
            {
                "id": "athos-hello-friendly",
                "name": "Athos Hello (Friendly)",
            },
            {
                "id": "athos-hello-formal",
                "name": "Athos Hello (Formal)",
            },
        ]

    async def on_startup(self) -> None:  # pragma: no cover - container callback
        """Called when the pipeline server boots."""

    async def on_shutdown(self) -> None:  # pragma: no cover - container callback
        """Called when the pipeline server shuts down."""

    async def on_valves_updated(self) -> None:
        """Hook invoked when valves are modified in the UI."""
        # No dynamic state yet, but keeping the hook makes future Athos flow
        # wiring straightforward.

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[dict, str, Generator[str, None, None], Iterator[str], Iterable[str]]:
        """Return a deterministic greeting tailored to the requested model."""

        del messages  # The history is unused for this demo pipeline.

        greetings = {
            "athos-hello-friendly": (
                "{prefix}, friend! I'm excited to chat about "
                "'{user_message}'."
            ),
            "athos-hello-formal": (
                "{prefix}. This is Athos. I acknowledge your message: "
                "'{user_message}'."
            ),
        }

        template = greetings.get(
            model_id,
            "{prefix}. Athos has not been configured for model '{model}'.",
        )

        timestamp = (
            time.strftime("%Y-%m-%d %H:%M:%S") if self.valves.include_timestamp else ""
        )
        prefix = self.valves.greeting_prefix
        content = template.format(prefix=prefix, user_message=user_message, model=model_id)
        if timestamp:
            content = f"[{timestamp}] {content}"

        if body.get("stream"):
            return self._build_stream(model_id=model_id, content=content)

        return self._build_sync_response(model_id=model_id, content=content)

    def _build_sync_response(self, *, model_id: str, content: str) -> dict:
        """Construct an OpenAI-compatible chat completion response."""

        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                }
            ],
        }

    def _build_stream(
        self, *, model_id: str, content: str
    ) -> Generator[str, None, None]:
        """Yield Server-Sent Events that mimic the OpenAI streaming protocol."""

        chunk_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(time.time())

        for token in content.split():
            data = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": f"{token} "},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(data)}\n\n"

        final = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        yield f"data: {json.dumps(final)}\n\n"
        yield "data: [DONE]\n\n"
