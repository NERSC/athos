"""Session model used by the runtime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FlowSession(BaseModel):
    """Mutable session state maintained across flow executions."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_id: str
    messages: List[dict] = Field(default_factory=list)
    workspace: Path = Field(default_factory=lambda: Path("/tmp"))
    interface: str = "unknown"
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Append a message to the conversation history and update timestamps."""

        message = {"role": role, "content": content, **kwargs}
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_history(self, limit: Optional[int] = None) -> List[dict]:
        """Return a copy of the most recent conversation history."""

        if limit is not None:
            return self.messages[-limit:]
        return self.messages.copy()

    def clear_history(self) -> None:
        """Clear stored conversation history and custom session state."""

        self.messages.clear()
        self.state.clear()
        self.updated_at = datetime.now()
