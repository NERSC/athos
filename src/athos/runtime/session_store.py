"""Session store abstractions for managing flow sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from athos.models.session import FlowSession


class SessionStore(ABC):
    """Abstract interface for session persistence backends."""

    @abstractmethod
    async def get_or_create(
        self,
        session_id: str,
        user_id: str,
        **kwargs,
    ) -> FlowSession:
        """Retrieve an existing session or create a new one."""

    @abstractmethod
    async def save(self, session: FlowSession) -> None:
        """Persist a session instance."""

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Remove a session from persistence."""

    @abstractmethod
    async def list_sessions(self, user_id: Optional[str] = None) -> list[str]:
        """Return known session identifiers, optionally filtered by user."""


class InMemorySessionStore(SessionStore):
    """In-memory session store suitable for tests and development."""

    def __init__(self) -> None:
        self._sessions: Dict[str, FlowSession] = {}

    async def get_or_create(
        self,
        session_id: str,
        user_id: str,
        **kwargs,
    ) -> FlowSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = FlowSession(
                session_id=session_id,
                user_id=user_id,
                **kwargs,
            )
        return self._sessions[session_id]

    async def save(self, session: FlowSession) -> None:
        self._sessions[session.session_id] = session

    async def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def list_sessions(self, user_id: Optional[str] = None) -> list[str]:
        if user_id is None:
            return list(self._sessions.keys())
        return [
            sid
            for sid, session in self._sessions.items()
            if session.user_id == user_id
        ]
