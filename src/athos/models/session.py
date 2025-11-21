"""Session model used by the runtime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    messages_from_dict,
    messages_to_dict,
)
from pydantic import BaseModel, ConfigDict, Field


class FlowSession(BaseModel):
    """Mutable session state maintained across flow executions."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_id: str
    messages: List[BaseMessage] = Field(default_factory=list)
    workspace: Path = Field(default_factory=lambda: Path("/tmp"))
    interface: str = "unknown"
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: BaseMessage) -> None:
        """Append a message to the conversation history and update timestamps.

        Args:
            message: LangChain BaseMessage instance to add to history
        """
        self.messages.append(message)
        self.updated_at = datetime.now()

    def add_user_message(self, content: str, **kwargs: Any) -> None:
        """Convenience method to add a user message to history.

        Args:
            content: Message content
            **kwargs: Additional arguments passed to HumanMessage constructor
        """
        self.add_message(HumanMessage(content=content, **kwargs))

    def add_assistant_message(self, content: str, **kwargs: Any) -> None:
        """Convenience method to add an assistant message to history.

        Args:
            content: Message content
            **kwargs: Additional arguments passed to AIMessage constructor
        """
        self.add_message(AIMessage(content=content, **kwargs))

    def add_system_message(self, content: str, **kwargs: Any) -> None:
        """Convenience method to add a system message to history.

        Args:
            content: Message content
            **kwargs: Additional arguments passed to SystemMessage constructor
        """
        self.add_message(SystemMessage(content=content, **kwargs))

    def add_tool_message(
        self, content: str, tool_call_id: str, name: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Convenience method to add a tool message to history.

        Args:
            content: Tool output content
            tool_call_id: ID of the tool call this message responds to
            name: Name of the tool
            **kwargs: Additional arguments passed to ToolMessage constructor
        """
        self.add_message(ToolMessage(content=content, tool_call_id=tool_call_id, name=name, **kwargs))

    def get_history(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """Return a copy of the most recent conversation history.

        Args:
            limit: Optional limit on number of recent messages to return

        Returns:
            List of LangChain BaseMessage objects
        """
        if limit is not None:
            return self.messages[-limit:]
        return self.messages.copy()

    def clear_history(self) -> None:
        """Clear stored conversation history and custom session state."""
        self.messages.clear()
        self.state.clear()
        self.updated_at = datetime.now()

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Serialize session for storage, converting BaseMessage to dict format.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        data = super().model_dump(**kwargs)
        # Convert BaseMessage objects to dicts using LangChain's serialization
        data["messages"] = messages_to_dict(self.messages)
        # Convert Path to string for JSON serialization
        data["workspace"] = str(self.workspace)
        return data

    @classmethod
    def model_validate(cls, obj: Any) -> FlowSession:
        """Deserialize session from storage, converting dict to BaseMessage format.

        Args:
            obj: Dictionary or object to validate and convert

        Returns:
            FlowSession instance with BaseMessage objects
        """
        if isinstance(obj, dict):
            # Convert dict messages back to BaseMessage objects
            if "messages" in obj:
                obj["messages"] = messages_from_dict(obj["messages"])
            # Convert string workspace back to Path
            if "workspace" in obj and isinstance(obj["workspace"], str):
                obj["workspace"] = Path(obj["workspace"])
        return super().model_validate(obj)
