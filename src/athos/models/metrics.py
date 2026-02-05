"""Lightweight execution metrics schema and helpers."""

from __future__ import annotations

from typing import Any, List, Mapping, Optional

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage captured from a model call."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


class ExecutionMetrics(BaseModel):
    """Normalized metrics attached to flow executions."""

    token_usage: Optional[TokenUsage] = None
    latency_ms: Optional[float] = Field(default=None, ge=0)
    tool_calls: List[str] = Field(default_factory=list)

    def to_metadata(self) -> dict:
        """Serialize to a metadata dictionary."""
        data = self.model_dump(exclude_none=True)
        # Drop empty tool_calls to keep metadata tidy.
        if not data.get("tool_calls"):
            data.pop("tool_calls", None)
        return data

    @classmethod
    def from_output_metadata(cls, metadata: Optional[Mapping[str, Any]]) -> Optional["ExecutionMetrics"]:
        """Build metrics from flow output metadata if present.

        Returns None when no recognizable metrics are found.
        """
        if not metadata or not isinstance(metadata, Mapping):
            return None

        token_usage = _coerce_token_usage(metadata.get("token_usage"))
        tool_calls = _coerce_tool_calls(metadata.get("tool_calls"))

        latency_ms = metadata.get("latency_ms")
        if latency_ms is not None:
            try:
                latency_ms = float(latency_ms)
            except (TypeError, ValueError):
                latency_ms = None

        if not token_usage and latency_ms is None and not tool_calls:
            return None

        return cls(token_usage=token_usage, latency_ms=latency_ms, tool_calls=tool_calls)


def _coerce_token_usage(raw: Any) -> Optional[TokenUsage]:
    """Normalize various token usage payloads into TokenUsage."""
    if not isinstance(raw, Mapping):
        return None

    input_tokens = raw.get("input_tokens", 0) or 0
    output_tokens = raw.get("output_tokens", 0) or 0

    try:
        input_tokens = int(input_tokens)
        output_tokens = int(output_tokens)
    except (TypeError, ValueError):
        return None

    if input_tokens == 0 and output_tokens == 0:
        return None

    return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)


def _coerce_tool_calls(raw: Any) -> List[str]:
    """Normalize tool call metadata to a simple list of tool names."""
    if raw is None:
        return []

    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str)]
    return [raw] if isinstance(raw, str) else []
