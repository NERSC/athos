"""Canonical message model used across ATHOS."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MessageRole(str, Enum):
    """Supported message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    """Internal message shape used for sessions and flow inputs."""

    model_config = ConfigDict(frozen=True)

    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    additional_kwargs: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_role(cls, value: Any) -> Any:
        """Allow initializing with role strings instead of MessageRole."""
        if isinstance(value, dict) and "role" in value and not isinstance(
            value["role"], MessageRole
        ):
            value = dict(value)
            value["role"] = MessageRole(value["role"])
        return value

    @property
    def text(self) -> str:
        """Convenience accessor for textual content."""
        return self.content

    def to_langchain(self) -> BaseMessage:
        """Convert to a LangChain message."""
        kwargs: Dict[str, Any] = {}
        if self.metadata:
            kwargs["metadata"] = self.metadata
        if self.additional_kwargs:
            kwargs["additional_kwargs"] = self.additional_kwargs
        if self.id:
            kwargs["id"] = self.id

        if self.role is MessageRole.USER:
            return HumanMessage(content=self.content, **kwargs)

        if self.role is MessageRole.ASSISTANT:
            ai_kwargs = dict(kwargs)
            if self.tool_calls is not None:
                ai_kwargs["tool_calls"] = self.tool_calls
            return AIMessage(content=self.content, **ai_kwargs)

        if self.role is MessageRole.SYSTEM:
            return SystemMessage(content=self.content, **kwargs)

        return ToolMessage(
            content=self.content,
            name=self.name,
            tool_call_id=self.tool_call_id,
            **kwargs,
        )

    @classmethod
    def from_langchain(cls, message: BaseMessage) -> Message:
        """Build an internal Message from a LangChain message."""
        common_kwargs: Dict[str, Any] = {}
        if getattr(message, "metadata", None):
            common_kwargs["metadata"] = dict(message.metadata)
        if getattr(message, "additional_kwargs", None):
            common_kwargs["additional_kwargs"] = dict(message.additional_kwargs)
        if getattr(message, "id", None):
            common_kwargs["id"] = message.id

        if isinstance(message, HumanMessage):
            return cls(role=MessageRole.USER, content=message.content, **common_kwargs)

        if isinstance(message, AIMessage):
            tool_calls = getattr(message, "tool_calls", None)
            # Some providers encode tool calls inside additional_kwargs
            if tool_calls is None:
                tool_calls = message.additional_kwargs.get("tool_calls") if getattr(message, "additional_kwargs", None) else None
            return cls(
                role=MessageRole.ASSISTANT,
                content=message.content,
                tool_calls=tool_calls,
                **common_kwargs,
            )

        if isinstance(message, SystemMessage):
            return cls(role=MessageRole.SYSTEM, content=message.content, **common_kwargs)

        if isinstance(message, ToolMessage):
            return cls(
                role=MessageRole.TOOL,
                content=message.content,
                name=message.name,
                tool_call_id=message.tool_call_id,
                **common_kwargs,
            )

        raise TypeError(f"Unsupported LangChain message type: {type(message)!r}")

    @classmethod
    def to_langchain_list(cls, messages: Sequence[Message]) -> List[BaseMessage]:
        """Convert a sequence of internal messages to LangChain messages."""
        return [msg.to_langchain() for msg in messages]

    @classmethod
    def from_langchain_list(cls, messages: Iterable[BaseMessage]) -> List[Message]:
        """Convert LangChain messages to internal Message objects."""
        return [cls.from_langchain(msg) for msg in messages]
