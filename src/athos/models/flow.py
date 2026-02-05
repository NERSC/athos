"""Flow input and output models."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from athos.models.enums import ExecutionMode
from athos.models.message import Message
from athos.models.session import FlowSession


class Artifact(BaseModel):
    """Structured representation of a non-text artifact produced by a flow."""

    model_config = ConfigDict(frozen=True)

    type: str
    path: Optional[str] = None
    data: Optional[Any] = None
    display_name: str = ""
    metadata: dict = Field(default_factory=dict)


class FlowOutput(BaseModel):
    """Structured output returned from a flow execution."""

    model_config = ConfigDict(frozen=True)

    content: str
    artifacts: List[Artifact] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class FlowInput(BaseModel):
    """Rich input payload provided to flow implementations."""

    model_config = ConfigDict(frozen=True)

    message: Message
    session: FlowSession
    mode: ExecutionMode
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _coerce_message(cls, value: dict) -> dict:
        """Allow initializing with plain user strings."""
        if isinstance(value, dict) and isinstance(value.get("message"), str):
            coerced = dict(value)
            coerced["message"] = Message(role="user", content=value["message"])
            return coerced
        return value
