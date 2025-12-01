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
    """Rich input payload provided to flow implementations.

    TODO: Consider migrating message field to BaseMessage for multimodal support.
    This would enable:
    - Image inputs for vision models
    - File attachments in conversations
    - Rich tool result formatting
    - Consistent typing with session.messages (List[BaseMessage])

    Migration would require:
    1. Change FlowRunner.execute(message: str | BaseMessage)
    2. Change FlowInput.message: BaseMessage
    3. Add .text property for flows that only need text
    4. Update _record_interaction() to handle BaseMessage directly
    """

    model_config = ConfigDict(frozen=True)

    # Currently a simple string for text-only use cases.
    # Future: Migrate to BaseMessage to support multimodal inputs.
    message: str
    session: FlowSession
    mode: ExecutionMode
    metadata: dict = Field(default_factory=dict)
