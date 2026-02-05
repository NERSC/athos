"""Session model used by the runtime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from athos.models.message import Message, MessageRole


class FlowSession(BaseModel):
    """Mutable session state maintained across flow executions."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    workspace: Path = Field(default_factory=lambda: Path("/tmp"))
    interface: str = "unknown"
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """Append a message to the conversation history and update timestamps."""

        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_user_message(self, content: str, **kwargs: Any) -> None:
        """Add a user message to history."""
        self.add_message(Message(role=MessageRole.USER, content=content, **kwargs))

    def add_assistant_message(self, content: str, **kwargs: Any) -> None:
        """Add an assistant message to history."""
        self.add_message(Message(role=MessageRole.ASSISTANT, content=content, **kwargs))

    def add_system_message(self, content: str, **kwargs: Any) -> None:
        """Add a system message to history."""
        self.add_message(Message(role=MessageRole.SYSTEM, content=content, **kwargs))

    def add_tool_message(
        self, content: str, tool_call_id: str, name: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Add a tool message to history."""
        self.add_message(
            Message(
                role=MessageRole.TOOL,
                content=content,
                tool_call_id=tool_call_id,
                name=name,
                **kwargs,
            )
        )

    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """Return a copy of the most recent conversation history."""

        if limit is not None:
            return self.messages[-limit:]
        return self.messages.copy()

    def clear_history(self) -> None:
        """Clear stored conversation history and custom session state."""

        self.messages.clear()
        self.state.clear()
        self.updated_at = datetime.now()

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Serialize session with JSON-friendly fields."""
        data = super().model_dump(**kwargs)
        if "workspace" in data and isinstance(self.workspace, Path):
            data["workspace"] = str(self.workspace)
        return data

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "FlowSession":
        """Deserialize session, normalizing workspace paths."""
        if isinstance(obj, dict) and "workspace" in obj and isinstance(obj["workspace"], str):
            normalized = dict(obj)
            normalized["workspace"] = Path(obj["workspace"])
            return super().model_validate(normalized, **kwargs)
        return super().model_validate(obj, **kwargs)
