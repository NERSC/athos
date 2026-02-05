"""Execution request and result models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from athos.models.enums import ExecutionMode
from athos.models.message import Message
from athos.models.flow import FlowOutput


class FlowRequest(BaseModel):
    """Internal request model used by the flow runner."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    flow_name: str
    message: Message
    session_id: str
    user_id: str
    mode: ExecutionMode
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="before")
    @classmethod
    def _coerce_message(cls, value: dict) -> dict:
        """Allow initializing with plain user strings."""
        if isinstance(value, dict) and isinstance(value.get("message"), str):
            coerced = dict(value)
            coerced["message"] = Message(role="user", content=value["message"])
            return coerced
        return value


class FlowResult(BaseModel):
    """Result object produced after executing a flow request."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    session_id: str
    success: bool
    output: Optional[FlowOutput] = None
    error: Optional[str] = None
    execution_time: float
    metadata: dict = Field(default_factory=dict)
