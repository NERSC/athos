"""Flow input and output models."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from athos.models.session import FlowSession
from athos.models.enums import ExecutionMode


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

    message: str
    session: FlowSession
    mode: ExecutionMode
    metadata: dict = Field(default_factory=dict)
