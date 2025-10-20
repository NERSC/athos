# ATHOS OpenWebUI Pipelines Integration Plan (v2.1)

## Executive Summary

This plan details the integration of OpenWebUI Pipelines support into ATHOS with a **redesigned Flow and Runner architecture**. The design introduces rich, structured interfaces that separate concerns cleanly while enabling advanced features like streaming, artifacts, and session management.

The integration leverages:
- **Alpha Berkeley** patterns for sophisticated OpenWebUI integration (valves, streaming, status events)
- **LangGraph Pipeline** patterns for clean framework-agnostic streaming
- **Existing ATHOS** architecture (flows, registry, configuration system)
- **New rich interfaces** for flows, sessions, and results

## Architecture Principles

1. **Flows are Stateless**: Pure functions over `(input, session) -> output`
2. **Runner Manages Lifecycle**: Orchestration, sessions, hooks, errors
3. **Rich Structured I/O**: Typed inputs/outputs with metadata and artifacts
4. **Session Externalization**: State lives outside flows in pluggable stores
5. **Streaming First-Class**: Built into interfaces, not bolted on
6. **Framework Flexibility**: Support both LangGraph and Smolagents transparently
7. **LangGraph Integration**: Let LangGraph manage its own checkpointing, we coordinate
8. **Start Simple, Extend Later**: Begin with basic execution, add features incrementally
9. **Backward Compatible**: Existing flows work during migration

## Design Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenWebUI Frontend                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/SSE
┌────────────────────────▼────────────────────────────────────┐
│              OpenWebUI Pipelines Server                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         athos_pipeline.py (Pipeline class)           │  │
│  │  • pipe() method (OpenWebUI protocol)                │  │
│  │  • Valves for configuration                          │  │
│  │  • Format FlowOutput → OpenWebUI events              │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────┐
│                  ATHOS Runtime (NEW)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   FlowRunner (athos.runtime.runner)                  │  │
│  │   • execute() - sync execution                       │  │
│  │   • stream() - async streaming                       │  │
│  │   • Session management via SessionStore              │  │
│  │   • Hook system for observability                    │  │
│  │   • Lifecycle orchestration                          │  │
│  └──────────┬────────────────────────┬──────────────────┘  │
│             │                        │                      │
│  ┌──────────▼─────────┐   ┌──────────▼──────────────────┐  │
│  │  SessionStore      │   │   HookManager               │  │
│  │  • In-memory       │   │   • BEFORE_EXECUTE          │  │
│  │  • Redis (future)  │   │   • OUTPUT_CHUNK            │  │
│  │  • Manages state   │   │   • AFTER_SUCCESS/ERROR     │  │
│  └────────────────────┘   └─────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Enhanced BaseFlow Interface                        │  │
│  │   • execute(FlowInput) -> FlowOutput                 │  │
│  │   • stream(FlowInput) -> AsyncGen[FlowOutput]        │  │
│  │   • initialize(config) - one-time setup              │  │
│  │   • cleanup() - resource cleanup                     │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │   Flow Implementations                               │  │
│  │   • LangGraphReactAgentFlow                         │  │
│  │   • LangGraphChatbotFlow                            │  │
│  │   • SmolAgentFlow                                    │  │
│  │   • ChatbotFlow                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Package Structure

Following the **flat models package** pattern for clean separation of concerns:

```
athos/
├── models/                        # All data models (NEW)
│   ├── __init__.py
│   ├── flow.py                   # FlowInput, FlowOutput, Artifact
│   ├── session.py                # FlowSession
│   ├── execution.py              # FlowRequest, FlowResult
│   └── enums.py                  # ExecutionMode
│
├── interfaces/
│   ├── __init__.py
│   └── base_flow.py              # BaseFlow (imports from models)
│
├── runtime/
│   ├── __init__.py
│   ├── runner.py                 # FlowRunner (imports from models)
│   ├── session_store.py          # SessionStore (imports from models)
│   ├── hooks.py                  # HookManager (NEW)
│   ├── compat.py                 # Legacy compatibility (NEW)
│   └── builder.py                # Existing builder
│
├── integrations/
│   └── openwebui/
│       ├── __init__.py
│       ├── pipeline.py           # Pipeline class (NEW)
│       └── formatters.py         # Event formatting (NEW)
│
├── frameworks/
│   ├── langgraph/
│   │   ├── flows/
│   │   │   ├── chatbot.py       # Refactored
│   │   │   └── react_agent.py   # Refactored
│   │   ├── factories.py
│   │   └── utils/
│   │       ├── messages.py
│   │       └── translation.py   # LangGraph ↔ ATHOS translation (NEW)
│   └── smolagents/
│       └── flows/
│
├── config/
│   └── models.py                 # Existing Pydantic configs
│
└── ...
```

**Key Benefits**:
- ✅ **No circular dependencies**: `models/` has no imports from other ATHOS packages
- ✅ **Clear layering**: Models → Interfaces → Runtime → Integrations
- ✅ **Easy imports**: `from athos.models.flow import FlowInput, FlowOutput`
- ✅ **Standard pattern**: Similar to Django, FastAPI, etc.

## Core Data Models

All models live in `athos/models/` for clean dependency management.

### FlowInput: Rich Input to Flows

**File**: `athos/src/athos/models/flow.py`

```python
from dataclasses import dataclass, field
from typing import Optional, Any
from athos.models.session import FlowSession
from athos.models.enums import ExecutionMode

@dataclass
class FlowInput:
    """
    Rich input passed to flows.

    Provides everything a flow needs without coupling to interfaces.
    """
    message: str                    # User's message/query
    session: FlowSession            # Session state (history, workspace)
    mode: ExecutionMode             # SYNC, STREAMING, INTERACTIVE
    metadata: dict = field(default_factory=dict)  # Per-request extras
```

**Key Benefits**:
- **Single parameter**: Flows receive one structured input instead of many args
- **Extensible**: Add new fields without breaking existing flows
- **Testable**: Easy to create test inputs with controlled state
- **LangGraph-friendly**: Can pass LangGraph config via `metadata["langgraph_config"]`

### FlowOutput: Structured Results

**File**: `athos/src/athos/models/flow.py`

```python
from dataclasses import dataclass, field
from typing import Optional, Any, List

@dataclass
class Artifact:
    """Something the flow produced beyond text."""
    type: str                       # "image", "file", "data", "link"
    path: Optional[str] = None      # For files/images
    data: Optional[Any] = None      # For inline data
    display_name: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize for logging/transmission."""
        return {
            "type": self.type,
            "path": self.path,
            "display_name": self.display_name,
            "metadata": self.metadata,
        }


@dataclass
class FlowOutput:
    """
    Structured output from flows.

    Supports text, artifacts (images/files), and metadata.
    """
    content: str                    # Primary text response
    artifacts: List[Artifact] = field(default_factory=list)  # Images, plots, files, links
    metadata: dict = field(default_factory=dict)  # Execution details (tokens, tools used, etc.)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "metadata": self.metadata,
        }
```

**Key Benefits**:
- **Structured artifacts**: Separate plots/files from text
- **Rich metadata**: Track tokens, tool calls, performance
- **OpenWebUI formatting**: Pipeline knows how to render artifacts
- **LangGraph events**: Metadata can carry event_type, streaming flags, etc.

### FlowSession: External State Management

**File**: `athos/src/athos/models/session.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

@dataclass
class FlowSession:
    """
    Session state managed by Runner (not flows).

    Persists conversation history and custom state across invocations.
    """
    session_id: str
    user_id: str

    # Conversation history (framework-neutral)
    messages: List[dict] = field(default_factory=list)  # [{"role": "user", "content": "..."}, ...]

    # Workspace for files
    workspace: Path = field(default_factory=lambda: Path("/tmp"))

    # Interface context
    interface: str = "unknown"  # "openwebui", "cli", "slackbot"

    # Custom state (flows can store anything here)
    # LangGraph flows can use state["langgraph_state"] for extra state
    state: dict = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add message to history."""
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        self.updated_at = datetime.now()

    def get_history(self, limit: Optional[int] = None) -> List[dict]:
        """Get recent message history."""
        if limit:
            return self.messages[-limit:]
        return self.messages.copy()

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
        self.state.clear()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Serialize for persistence."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": self.messages,
            "workspace": str(self.workspace),
            "interface": self.interface,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlowSession":
        """Deserialize from persistence."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            messages=data.get("messages", []),
            workspace=Path(data.get("workspace", "/tmp")),
            interface=data.get("interface", "unknown"),
            state=data.get("state", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )
```

**Key Benefits**:
- **Flow-agnostic history**: Works with any framework
- **Workspace isolation**: Per-session file storage
- **Pluggable persistence**: In-memory, Redis, DB
- **Flows stay stateless**: State lives externally
- **LangGraph-friendly**: `state["langgraph_state"]` for framework-specific state

### Execution Models (Internal to Runtime)

**File**: `athos/src/athos/models/execution.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from athos.models.flow import FlowOutput
from athos.models.enums import ExecutionMode

@dataclass
class FlowRequest:
    """Internal request model for Runner."""
    request_id: str
    flow_name: str
    message: str
    session_id: str
    user_id: str
    mode: ExecutionMode
    metadata: dict
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FlowResult:
    """Result of flow execution via Runner."""
    request_id: str
    success: bool
    output: Optional[FlowOutput]
    error: Optional[str]
    execution_time: float
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "output": self.output.to_dict() if self.output else None,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }
```

### Enums

**File**: `athos/src/athos/models/enums.py`

```python
from enum import Enum

class ExecutionMode(str, Enum):
    """How the flow should be executed."""
    SYNC = "sync"                   # Single execute() call
    STREAMING = "streaming"         # Stream updates incrementally
    INTERACTIVE = "interactive"     # Multi-turn with interrupts (future)
```

## Enhanced BaseFlow Interface

**File**: `athos/src/athos/interfaces/base_flow.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from athos.models.flow import FlowInput, FlowOutput
from athos.models.enums import ExecutionMode

class BaseFlow(ABC):
    """
    Enhanced base flow interface.

    Flows are now PURE FUNCTIONS: (input, session) -> output
    State lives in FlowSession, not in flow instance.
    """

    # Class-level metadata
    name: str = "base_flow"
    description: str = "Base flow"
    supported_modes: list[ExecutionMode] = [ExecutionMode.SYNC]

    @abstractmethod
    async def execute(self, input: FlowInput) -> FlowOutput:
        """
        Execute the flow once and return structured output.

        PRIMARY INTERFACE - all flows must implement.
        Even streaming flows should have working execute() for testing.
        """
        raise NotImplementedError

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """
        Stream execution with intermediate updates.

        Default: execute once and yield result.
        Override for true streaming.
        """
        result = await self.execute(input)
        yield result

    async def initialize(self, config) -> None:
        """
        One-time initialization with configuration.

        Called by Runner when flow is first loaded.
        Use for expensive setup (model loading, MCP connections).
        """
        pass

    async def cleanup(self) -> None:
        """
        Clean up resources.

        Called by Runner when flow is unloaded.
        Guaranteed to be called even on errors.
        """
        pass

    def can_stream(self) -> bool:
        """Does this flow support streaming?"""
        return ExecutionMode.STREAMING in self.supported_modes
```

**Key Changes from Current**:
- ✅ **Rich input**: `FlowInput` instead of `str`
- ✅ **Structured output**: `FlowOutput` instead of `Any`
- ✅ **Streaming built-in**: `stream()` method for frameworks that support it
- ✅ **Lifecycle hooks**: `initialize()` and `cleanup()` for resource management
- ✅ **Metadata**: Class-level `name`, `description`, `supported_modes`

## LangGraph Integration Strategy

### Message Translation Utilities

**File**: `athos/src/athos/frameworks/langgraph/utils/translation.py`

```python
"""Translation utilities between ATHOS and LangGraph formats."""

from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage


def to_langgraph_messages(session_messages: List[dict]) -> List[BaseMessage]:
    """
    Convert ATHOS session messages to LangGraph format.

    Args:
        session_messages: List of dicts with {"role": "user|assistant|system", "content": "..."}

    Returns:
        List of LangChain message objects
    """
    result = []
    for msg in session_messages:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))

    return result


def from_langgraph_messages(langgraph_messages: List[BaseMessage]) -> List[dict]:
    """
    Convert LangGraph messages to ATHOS session format.

    Args:
        langgraph_messages: List of LangChain message objects

    Returns:
        List of dicts with {"role": "user|assistant|system", "content": "..."}
    """
    result = []
    for msg in langgraph_messages:
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, SystemMessage):
            result.append({"role": "system", "content": msg.content})

    return result


def build_langgraph_config(session_id: str, metadata: Dict[str, Any] = None) -> dict:
    """
    Build LangGraph config dict from ATHOS session info.

    Args:
        session_id: ATHOS session ID (used as LangGraph thread_id)
        metadata: Optional metadata that may contain LangGraph-specific config

    Returns:
        Config dict for LangGraph execution
    """
    config = {
        "configurable": {
            "thread_id": session_id  # LangGraph uses thread_id for checkpointing
        }
    }

    # Allow passing LangGraph-specific config via metadata
    if metadata and "langgraph_config" in metadata:
        config.update(metadata["langgraph_config"])

    return config
```

### Integration Approach

**LangGraph flows will:**

1. **Use LangGraph's own checkpointing** via `thread_id = session_id`
2. **Sync conversation history** to `FlowSession.messages` for consistency
3. **Store extra state** in `FlowSession.state["langgraph_state"]` if needed
4. **Translate messages** using utilities from `translation.py`
5. **Wrap LangGraph events** in `FlowOutput` for consistent interface

This approach:
- ✅ Leverages LangGraph's robust checkpointing system
- ✅ Maintains compatibility with other ATHOS components
- ✅ Keeps flows framework-agnostic from Runner's perspective
- ✅ Allows LangGraph-specific config via metadata

## Milestone Breakdown

### Milestone 1: Core Runtime Foundation (Week 1-2)

**Goal**: Establish the new runtime models and basic FlowRunner without breaking existing flows.

#### Task 1.1: Create Models Package

**New Files**:
- `athos/src/athos/models/__init__.py`
- `athos/src/athos/models/enums.py`
- `athos/src/athos/models/flow.py`
- `athos/src/athos/models/session.py`
- `athos/src/athos/models/execution.py`

**Implementation**:

1. **Enums** (`enums.py`):
```python
from enum import Enum

class ExecutionMode(str, Enum):
    SYNC = "sync"
    STREAMING = "streaming"
    INTERACTIVE = "interactive"
```

2. **Flow Models** (`flow.py`):
```python
# FlowInput, FlowOutput, Artifact
# (Full implementations shown above)
```

3. **Session Model** (`session.py`):
```python
# FlowSession with methods
# (Full implementation shown above)
```

4. **Execution Models** (`execution.py`):
```python
# FlowRequest, FlowResult
# (Full implementations shown above)
```

5. **Package Init** (`__init__.py`):
```python
"""ATHOS data models."""

from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput, Artifact
from athos.models.session import FlowSession
from athos.models.execution import FlowRequest, FlowResult

__all__ = [
    "ExecutionMode",
    "FlowInput",
    "FlowOutput",
    "Artifact",
    "FlowSession",
    "FlowRequest",
    "FlowResult",
]
```

**Tests**: `tests/models/test_*.py`
- Serialization/deserialization (`to_dict`, `from_dict`)
- FlowSession message management
- Artifact creation and metadata
- All models are immutable where expected

#### Task 1.2: Create SessionStore Abstraction

**File**: `athos/src/athos/runtime/session_store.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
from athos.models.session import FlowSession

class SessionStore(ABC):
    """Abstract session persistence."""

    @abstractmethod
    async def get_or_create(
        self,
        session_id: str,
        user_id: str,
        **kwargs
    ) -> FlowSession:
        """Get existing session or create new one."""
        pass

    @abstractmethod
    async def save(self, session: FlowSession) -> None:
        """Persist session state."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete a session."""
        pass

    @abstractmethod
    async def list_sessions(self, user_id: Optional[str] = None) -> list[str]:
        """List all session IDs, optionally filtered by user."""
        pass


class InMemorySessionStore(SessionStore):
    """Simple in-memory session storage for development."""

    def __init__(self):
        self._sessions: Dict[str, FlowSession] = {}

    async def get_or_create(
        self,
        session_id: str,
        user_id: str,
        **kwargs
    ) -> FlowSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = FlowSession(
                session_id=session_id,
                user_id=user_id,
                **kwargs
            )
        return self._sessions[session_id]

    async def save(self, session: FlowSession) -> None:
        self._sessions[session.session_id] = session

    async def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def list_sessions(self, user_id: Optional[str] = None) -> list[str]:
        if user_id:
            return [
                sid for sid, sess in self._sessions.items()
                if sess.user_id == user_id
            ]
        return list(self._sessions.keys())
```

**Tests**: `tests/runtime/test_session_store.py`
- Create and retrieve sessions
- Save and load session state
- Session isolation (different users/sessions)
- List sessions with filtering

#### Task 1.3: Update BaseFlow Interface

**File**: `athos/src/athos/interfaces/base_flow.py`

(Full implementation shown in "Enhanced BaseFlow Interface" section above)

**Tests**: `tests/interfaces/test_base_flow.py`
- Abstract methods raise NotImplementedError
- Default `stream()` calls `execute()`
- `can_stream()` checks supported_modes

#### Task 1.4: Create Basic FlowRunner

**File**: `athos/src/athos/runtime/runner.py`

```python
import time
import uuid
import logging
from typing import Optional, Dict, AsyncGenerator
from pathlib import Path

from athos.config.models import AthosConfig
from athos.models.execution import FlowRequest, FlowResult
from athos.models.flow import FlowInput, FlowOutput
from athos.models.session import FlowSession
from athos.models.enums import ExecutionMode
from athos.runtime.session_store import SessionStore, InMemorySessionStore
from athos.interfaces.base_flow import BaseFlow
from athos.runtime.builder import build_flow

logger = logging.getLogger(__name__)


class FlowRunner:
    """
    Orchestrates flow lifecycle and session management.

    Responsibilities:
    - Load and cache flow instances
    - Manage sessions via SessionStore
    - Execute flows with proper lifecycle
    - Handle errors consistently
    - Emit hooks for observability (added in M4)
    """

    def __init__(
        self,
        config: AthosConfig,
        session_store: Optional[SessionStore] = None,
    ):
        self.config = config
        self.session_store = session_store or InMemorySessionStore()

        self._flow_cache: Dict[str, BaseFlow] = {}

    async def execute(
        self,
        flow_name: str,
        message: str,
        session_id: str,
        user_id: str,
        *,
        mode: ExecutionMode = ExecutionMode.SYNC,
        interface: str = "unknown",
        metadata: Optional[dict] = None,
    ) -> FlowResult:
        """
        Execute a flow synchronously and return result.

        Args:
            flow_name: Name of flow to execute
            message: User message/query
            session_id: Session identifier for conversation continuity
            user_id: User identifier for workspace isolation
            mode: Execution mode (SYNC, STREAMING, INTERACTIVE)
            interface: Interface calling this ("openwebui", "cli", etc.)
            metadata: Extra per-request data

        Returns:
            FlowResult with success/output/error
        """
        request = FlowRequest(
            request_id=self._generate_request_id(),
            flow_name=flow_name,
            message=message,
            session_id=session_id,
            user_id=user_id,
            mode=mode,
            metadata=metadata or {},
        )

        logger.info(
            f"[{request.request_id}] Executing flow '{flow_name}' "
            f"for user={user_id}, session={session_id}"
        )

        start_time = time.time()

        try:
            # Get or create session
            session = await self.session_store.get_or_create(
                session_id=session_id,
                user_id=user_id,
                workspace=self._get_workspace_path(user_id, session_id),
                interface=interface,
            )

            # Get or load flow
            flow = await self._get_flow(flow_name)

            # Build input
            flow_input = FlowInput(
                message=message,
                session=session,
                mode=mode,
                metadata=metadata or {},
            )

            # Execute
            logger.debug(f"[{request.request_id}] Calling flow.execute()")
            output = await flow.execute(flow_input)

            # Update session with new messages
            session.add_message("user", message)
            session.add_message("assistant", output.content)
            await self.session_store.save(session)

            execution_time = time.time() - start_time

            # Build result
            result = FlowResult(
                request_id=request.request_id,
                success=True,
                output=output,
                error=None,
                execution_time=execution_time,
                metadata={"flow_name": flow_name},
            )

            logger.info(
                f"[{request.request_id}] Flow succeeded in {execution_time:.2f}s"
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.exception(
                f"[{request.request_id}] Flow execution failed after {execution_time:.2f}s: {e}"
            )

            result = FlowResult(
                request_id=request.request_id,
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "flow_name": flow_name,
                    "exception_type": type(e).__name__
                },
            )

            return result

    async def stream(
        self,
        flow_name: str,
        message: str,
        session_id: str,
        user_id: str,
        *,
        interface: str = "unknown",
        metadata: Optional[dict] = None,
    ) -> AsyncGenerator[FlowOutput, None]:
        """
        Execute a flow with streaming.

        Yields FlowOutput objects as they're produced.
        Session is updated after streaming completes.
        """
        request = FlowRequest(
            request_id=self._generate_request_id(),
            flow_name=flow_name,
            message=message,
            session_id=session_id,
            user_id=user_id,
            mode=ExecutionMode.STREAMING,
            metadata=metadata or {},
        )

        logger.info(
            f"[{request.request_id}] Streaming flow '{flow_name}' "
            f"for user={user_id}, session={session_id}"
        )

        try:
            session = await self.session_store.get_or_create(
                session_id=session_id,
                user_id=user_id,
                workspace=self._get_workspace_path(user_id, session_id),
                interface=interface,
            )

            flow = await self._get_flow(flow_name)

            if not flow.can_stream():
                # Fallback to execute
                logger.warning(
                    f"[{request.request_id}] Flow '{flow_name}' doesn't support "
                    f"streaming, falling back to execute()"
                )
                output = await flow.execute(
                    FlowInput(message, session, ExecutionMode.SYNC, metadata or {})
                )
                yield output
            else:
                # True streaming
                flow_input = FlowInput(
                    message=message,
                    session=session,
                    mode=ExecutionMode.STREAMING,
                    metadata=metadata or {},
                )

                last_output = None
                async for output in flow.stream(flow_input):
                    last_output = output
                    yield output

                # Update session with final output
                if last_output:
                    session.add_message("user", message)
                    session.add_message("assistant", last_output.content)
                    await self.session_store.save(session)

            logger.info(f"[{request.request_id}] Streaming completed")

        except Exception as e:
            logger.exception(f"[{request.request_id}] Streaming failed: {e}")
            raise

    async def _get_flow(self, flow_name: str) -> BaseFlow:
        """Get or load a flow instance."""
        if flow_name in self._flow_cache:
            return self._flow_cache[flow_name]

        logger.debug(f"Loading flow '{flow_name}'")

        # Build flow using existing builder
        flow = build_flow(flow_name, self.config)

        # Initialize
        flow_config = self.config.flows[flow_name]
        await flow.initialize(flow_config)

        # Cache
        self._flow_cache[flow_name] = flow

        logger.debug(f"Flow '{flow_name}' loaded and initialized")

        return flow

    async def cleanup(self) -> None:
        """Clean up all cached flows."""
        logger.info(f"Cleaning up {len(self._flow_cache)} cached flows")

        for flow_name, flow in self._flow_cache.items():
            try:
                await flow.cleanup()
            except Exception as e:
                logger.warning(
                    f"Error cleaning up flow '{flow_name}': {e}"
                )

        self._flow_cache.clear()

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        return f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def _get_workspace_path(self, user_id: str, session_id: str) -> Path:
        """Get workspace path for session."""
        base = Path(getattr(self.config, 'workspace_path', None) or "/tmp/athos_workspace")
        return base / user_id / session_id
```

**Tests**: `tests/runtime/test_runner.py`
- Execute flow successfully
- Handle flow errors gracefully
- Session creation and reuse
- Flow caching
- Cleanup on shutdown

**Deliverables**:
- ✅ All models in `athos/models/` package
- ✅ SessionStore abstraction with in-memory impl
- ✅ Enhanced BaseFlow interface
- ✅ Basic FlowRunner (sync execution only)
- ✅ Comprehensive unit tests (90%+ coverage)
- ✅ Updated docs

---

### Milestone 2: Flow Migration & Compatibility (Week 2-3)

**Goal**: Create compatibility layer and migrate one flow to the new interface as proof of concept.

#### Task 2.1: Create Compatibility Shim

**File**: `athos/src/athos/runtime/compat.py`

```python
"""
Compatibility layer for existing flows.

Allows existing flows with execute(str) -> Any to work with new Runner.
"""

import logging
from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput

logger = logging.getLogger(__name__)


class LegacyFlowAdapter(BaseFlow):
    """
    Adapter that wraps old-style flows to work with new Runner.

    Usage:
        legacy_flow = OldChatbotFlow()
        adapted = LegacyFlowAdapter(legacy_flow)
        # Now works with FlowRunner
    """

    def __init__(self, legacy_flow):
        self._legacy_flow = legacy_flow

        # Copy metadata if available
        self.name = getattr(legacy_flow, 'name', legacy_flow.__class__.__name__)
        self.description = getattr(legacy_flow, 'description', '')

    async def execute(self, input: FlowInput) -> FlowOutput:
        """Call legacy execute(str) and wrap result."""
        # Call old interface
        if hasattr(self._legacy_flow, 'execute'):
            result = await self._legacy_flow.execute(input.message)
        else:
            raise AttributeError(f"Legacy flow {self._legacy_flow} has no execute method")

        # Wrap in new output format
        if isinstance(result, str):
            return FlowOutput(content=result)
        else:
            # Best-effort conversion
            return FlowOutput(content=str(result))

    async def cleanup(self) -> None:
        """Delegate to legacy close() if available."""
        if hasattr(self._legacy_flow, 'close'):
            await self._legacy_flow.close()


def is_new_interface(flow: BaseFlow) -> bool:
    """
    Check if flow uses new FlowInput/FlowOutput interface.

    Returns:
        True if flow uses new interface, False if legacy
    """
    import inspect

    if not hasattr(flow, 'execute'):
        return False

    sig = inspect.signature(flow.execute)
    params = list(sig.parameters.values())

    if len(params) != 1:
        return False

    # Check if parameter is annotated with FlowInput
    param_annotation = str(params[0].annotation)
    return 'FlowInput' in param_annotation
```

**Update FlowRunner** to auto-detect and adapt legacy flows:

```python
# In FlowRunner._get_flow()
async def _get_flow(self, flow_name: str) -> BaseFlow:
    if flow_name in self._flow_cache:
        return self._flow_cache[flow_name]

    flow = build_flow(flow_name, self.config)

    # Auto-detect legacy flows
    from athos.runtime.compat import is_new_interface, LegacyFlowAdapter

    if not is_new_interface(flow):
        logger.warning(
            f"Flow '{flow_name}' uses legacy interface, adapting"
        )
        flow = LegacyFlowAdapter(flow)

    await flow.initialize(self.config.flows[flow_name])
    self._flow_cache[flow_name] = flow

    return flow
```

**Tests**: `tests/runtime/test_compat.py`
- Legacy flow adapter wraps correctly
- Old flows work with new Runner
- Adapter handles errors gracefully

#### Task 2.2: Create LangGraph Translation Utilities

**File**: `athos/src/athos/frameworks/langgraph/utils/translation.py`

(Full implementation shown in "LangGraph Integration Strategy" section above)

**Tests**: `tests/frameworks/langgraph/test_translation.py`
- Message translation (both directions)
- Config building with metadata
- Handles edge cases (empty messages, unknown roles)

#### Task 2.3: Migrate LangGraph Chatbot Flow

**File**: `athos/src/athos/frameworks/langgraph/flows/chatbot.py` (refactored)

```python
"""Refactored LangGraph chatbot using new interface."""

from typing import Optional, AsyncGenerator
import logging

from athos.config.models import BaseFlowConfig
from athos.frameworks.langgraph.factories import build_model
from athos.frameworks.langgraph.utils.translation import (
    to_langgraph_messages,
    from_langgraph_messages,
)
from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.enums import ExecutionMode
from athos.registry.flow_registry import register_flow

logger = logging.getLogger(__name__)


class LangGraphChatbotFlow(BaseFlow):
    """
    Chatbot using new rich interface.

    Key changes from old version:
    - No internal _history (uses session.messages)
    - Returns FlowOutput instead of str
    - Supports streaming via stream() method
    - Stateless (can be shared across sessions)
    - Uses LangGraph's native message format internally
    """

    name = "langgraph_chatbot"
    description = "Simple conversational chatbot using LangGraph"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    def __init__(self):
        self.model = None
        self.system_prompt = None

    async def initialize(self, config: BaseFlowConfig) -> None:
        """Load model once during initialization."""
        # This gets called by FlowRunner with the flow config
        self.model = build_model(config.model)
        self.system_prompt = getattr(config, 'system_prompt', None)

        logger.info(
            f"Initialized {self.name} with model "
            f"{getattr(self.model, 'model_name', 'unknown')}"
        )

    async def execute(self, input: FlowInput) -> FlowOutput:
        """
        Single execution (non-streaming).

        Reads history from input.session, doesn't mutate internal state.
        """
        messages = self._build_messages(input)

        logger.debug(f"Invoking model with {len(messages)} messages")

        try:
            response = await self.model.ainvoke(messages)

            return FlowOutput(
                content=response.content,
                metadata={
                    "model": getattr(self.model, 'model_name', 'unknown'),
                    "tokens": getattr(response, 'usage', {})
                }
            )

        except Exception as e:
            logger.error(f"Model invocation failed: {e}")
            return FlowOutput(
                content=f"Error: {e}",
                metadata={"error": True}
            )

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """
        Streaming execution.

        Yields intermediate chunks as they're generated.
        """
        messages = self._build_messages(input)

        logger.debug(f"Streaming model with {len(messages)} messages")

        accumulated = ""
        try:
            async for chunk in self.model.astream(messages):
                chunk_content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                accumulated += chunk_content

                yield FlowOutput(
                    content=chunk_content,
                    metadata={"streaming": True, "chunk": True}
                )

            # Final complete output
            yield FlowOutput(
                content=accumulated,
                metadata={
                    "streaming": True,
                    "chunk": False,
                    "final": True,
                    "model": getattr(self.model, 'model_name', 'unknown'),
                }
            )

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield FlowOutput(
                content=f"Error: {e}",
                metadata={"error": True}
            )

    def _build_messages(self, input: FlowInput) -> list:
        """
        Build message list from session history.

        Uses input.session.messages instead of internal state.
        """
        from athos.frameworks.langgraph.utils.messages import (
            SystemMessage, HumanMessage
        )

        messages = []

        # System prompt
        if self.system_prompt:
            messages.append(SystemMessage(self.system_prompt))

        # History from session (convert to LangGraph format)
        messages.extend(to_langgraph_messages(input.session.get_history()))

        # Current message
        messages.append(HumanMessage(input.message))

        return messages

    async def cleanup(self) -> None:
        """No cleanup needed (model is lightweight)."""
        pass


# Register flow (config unchanged)
register_flow(
    "langgraph_chatbot",
    # ... existing config class ...
)
```

**Key Improvements**:
- ✅ **Stateless**: No `self._history`, reads from `input.session`
- ✅ **Rich output**: Returns `FlowOutput` with metadata
- ✅ **Streaming**: Implements true streaming via `stream()`
- ✅ **Lifecycle**: Uses `initialize()` for one-time setup
- ✅ **Shareable**: Same instance can serve multiple sessions
- ✅ **LangGraph-friendly**: Uses translation utilities

#### Task 2.4: Update CLI to Use Runner

**File**: `athos/src/athos/main.py` (updated)

```python
"""Updated CLI to use FlowRunner."""

import asyncio
from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner

async def cli_main(args):
    """CLI execution using new Runner."""
    # Load config
    config = build_config(args.config, overrides=args.overrides)

    # Create runner
    runner = FlowRunner(config)

    try:
        # Execute
        result = await runner.execute(
            flow_name=args.flow,
            message=args.input,
            session_id="cli_session",  # CLI uses single session
            user_id="cli_user",
            interface="cli",
            metadata={"cli": True}
        )

        if result.success:
            print(result.output.content)

            # Show artifacts if any
            for artifact in result.output.artifacts:
                print(f"\n[Artifact: {artifact.display_name}]")
                if artifact.type == "file":
                    print(f"  Path: {artifact.path}")
                elif artifact.type == "image":
                    print(f"  Image: {artifact.path}")
        else:
            print(f"Error: {result.error}")
            return 1

        return 0

    finally:
        await runner.cleanup()

# ... rest of CLI code ...
```

**Tests**: `tests/test_cli_integration.py`
- CLI executes flows via Runner
- Handles errors gracefully
- Shows artifacts appropriately

**Deliverables**:
- ✅ Compatibility shim for legacy flows
- ✅ LangGraph translation utilities
- ✅ One flow migrated (LangGraph chatbot)
- ✅ CLI updated to use Runner
- ✅ Tests demonstrating old and new flows work
- ✅ Migration guide documentation

---

### Milestone 3: Basic OpenWebUI Pipeline (Week 3-4)

**Goal**: Create minimal working OpenWebUI Pipeline using FlowRunner.

#### Task 3.1: Create Pipeline Module

**File**: `athos/src/athos/integrations/openwebui/pipeline.py`

```python
"""
OpenWebUI Pipeline for ATHOS.

Thin adapter that translates OpenWebUI protocol to FlowRunner calls.
"""

import asyncio
import time
import os
from typing import Optional, Generator, Union
from pathlib import Path
from pydantic import BaseModel, Field

from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner
from athos.models.flow import FlowOutput


class Pipeline:
    """
    OpenWebUI Pipeline for ATHOS flows.

    Responsibilities:
    - OpenWebUI protocol handling (pipe method)
    - Valve-based configuration
    - Format FlowOutput for OpenWebUI
    """

    class Valves(BaseModel):
        """User-configurable settings."""
        config_path: str = Field(
            default="config/config.yaml",
            description="Path to ATHOS configuration file"
        )
        default_flow: str = Field(
            default="hpc_chatbot",
            description="Default flow to execute"
        )
        enable_streaming: bool = Field(
            default=True,
            description="Enable streaming responses"
        )
        max_execution_time: int = Field(
            default=300,
            description="Maximum execution time in seconds"
        )

    def __init__(self):
        self.name = "ATHOS HPC Assistant"
        self.valves = self.Valves(
            **{k: os.getenv(k.upper(), v.default)
               for k, v in self.Valves.model_fields.items()}
        )

        self._runner: Optional[FlowRunner] = None
        self._initialized = False

    async def on_startup(self):
        """Initialize FlowRunner on startup."""
        if not self._initialized:
            # Load config
            config = build_config(self.valves.config_path)

            # Create runner
            self._runner = FlowRunner(config)

            self._initialized = True
            print(f"✓ ATHOS Pipeline initialized with flow: {self.valves.default_flow}")

    async def on_shutdown(self):
        """Clean up on shutdown."""
        if self._runner:
            await self._runner.cleanup()
        print("✓ ATHOS Pipeline shutdown")

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: list[dict],
        body: dict,
    ) -> Union[str, Generator]:
        """
        OpenWebUI pipe interface.

        Args:
            user_message: Latest user message
            model_id: Model ID (usually pipeline name)
            messages: Full conversation history
            body: Full request body with user info

        Returns:
            Generator yielding response chunks (if streaming enabled)
            or final response string
        """
        # Extract session info
        user_id = body.get("user", {}).get("id", "anonymous")
        chat_id = body.get("chat_id", f"chat_{int(time.time())}")

        # Use streaming if enabled
        if self.valves.enable_streaming:
            return self._execute_streaming(user_message, user_id, chat_id)
        else:
            return self._execute_sync(user_message, user_id, chat_id)

    def _execute_sync(self, message: str, user_id: str, session_id: str) -> str:
        """Non-streaming execution."""
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self._runner.execute(
                    flow_name=self.valves.default_flow,
                    message=message,
                    session_id=session_id,
                    user_id=user_id,
                    interface="openwebui",
                    metadata={"model_id": self.valves.default_flow}
                )
            )

            if result.success:
                return self._format_output(result.output)
            else:
                return f"❌ Error: {result.error}"

        finally:
            loop.close()

    def _execute_streaming(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> Generator:
        """Streaming execution."""

        def stream_generator():
            """Sync generator for OpenWebUI."""
            # Create event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Yield initial status
                yield self._create_status_event("Processing message...", done=False)

                # Stream from runner
                async def async_stream():
                    async for output in self._runner.stream(
                        flow_name=self.valves.default_flow,
                        message=message,
                        session_id=session_id,
                        user_id=user_id,
                        interface="openwebui",
                        metadata={"model_id": self.valves.default_flow}
                    ):
                        # Yield chunks
                        if output.metadata.get("chunk"):
                            # Intermediate chunk
                            yield output.content
                        else:
                            # Final output
                            yield self._format_output(output)

                # Run async stream
                gen = async_stream()
                while True:
                    try:
                        chunk = loop.run_until_complete(gen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break

                # Clear status
                yield self._create_status_event("", done=True)

            except Exception as e:
                # Clear status and show error
                yield self._create_status_event("", done=True)
                yield f"❌ Error: {str(e)}"

            finally:
                loop.close()

        return stream_generator()

    def _format_output(self, output: FlowOutput) -> str:
        """Format FlowOutput for OpenWebUI display."""
        parts = [output.content]

        # Add artifacts
        for artifact in output.artifacts:
            if artifact.type == "image":
                # Markdown image
                parts.append(
                    f"\n\n![{artifact.display_name}]({artifact.path})"
                )
            elif artifact.type == "file":
                # File link
                parts.append(
                    f"\n\n📄 [{artifact.display_name}]({artifact.path})"
                )
            elif artifact.type == "link":
                # Clickable link
                parts.append(
                    f"\n\n🔗 [{artifact.display_name}]({artifact.data})"
                )

        return "\n".join(parts)

    def _create_status_event(self, description: str, done: bool) -> dict:
        """Create OpenWebUI status event."""
        return {
            "event": {
                "type": "status",
                "data": {
                    "description": description,
                    "done": done,
                }
            }
        }
```

#### Task 3.2: Create Deployment Configuration

**File**: `athos/deployments/openwebui/docker-compose.yml`

```yaml
version: '3.8'

services:
  athos-pipeline:
    image: ghcr.io/open-webui/pipelines:main
    container_name: athos-pipeline
    restart: unless-stopped
    ports:
      - "9099:9099"
    volumes:
      - ../../src/athos:/app/athos
      - ../../config:/app/config
      - ./workspace:/app/workspace
    environment:
      - PIPELINES_DIR=/app/athos/integrations/openwebui
      - PYTHONPATH=/app
      - CONFIG_PATH=/app/config/config.yaml
      - DEFAULT_FLOW=hpc_chatbot
      - ENABLE_STREAMING=true

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    ports:
      - "3000:8080"
    environment:
      - OPENAI_API_BASE=http://athos-pipeline:9099
    depends_on:
      - athos-pipeline
```

**File**: `athos/deployments/openwebui/README.md`

```markdown
# ATHOS OpenWebUI Deployment

## Quick Start

1. Build and start services:
   ```bash
   cd athos/deployments/openwebui
   docker-compose up -d
   ```

2. Access OpenWebUI:
   - URL: http://localhost:3000
   - Configure pipeline in Settings > Connections

3. Configure ATHOS:
   - Edit `config/config.yaml` for flows and models
   - Restart pipeline: `docker-compose restart athos-pipeline`

## Configuration

### Valves (Runtime Config)
Adjust in OpenWebUI Settings > Pipelines > ATHOS:
- `config_path`: Path to ATHOS config
- `default_flow`: Which flow to execute
- `enable_streaming`: Enable/disable streaming
- `max_execution_time`: Timeout in seconds

### ATHOS Config
Edit `config/config.yaml`:
- Define models, MCP servers, tools
- Configure flows and their parameters

## Architecture

- **Pipeline**: Thin adapter translating OpenWebUI → ATHOS
- **FlowRunner**: Orchestrates flow execution and sessions
- **SessionStore**: Manages conversation history (in-memory)
- **Flows**: Your ATHOS flows (LangGraph, Smolagents, etc.)
```

**Deliverables**:
- ✅ Working Pipeline class
- ✅ Basic streaming support
- ✅ Artifact formatting
- ✅ Docker Compose deployment
- ✅ Integration tests with mock OpenWebUI requests
- ✅ Deployment documentation

---

### Milestone 4: Hook System & Enhanced Streaming (Week 4-5)

**Goal**: Add hook system for observability and improve streaming with status events.

(Implementation same as v2 plan - hooks integrated into FlowRunner, built-in hooks for logging/metrics, Pipeline updated to use hooks for status events)

**Deliverables**:
- ✅ Hook system with event types
- ✅ Built-in hooks (logging, metrics)
- ✅ Hook integration in FlowRunner
- ✅ Enhanced streaming with status events
- ✅ Tests for hook execution and error isolation
- ✅ Documentation on creating custom hooks

---

### Milestone 5: LangGraph Streaming & Advanced Features (Week 5-6)

**Goal**: Enable full LangGraph streaming with thinking blocks and tool call visibility.

#### Task 5.1: Enhance LangGraph ReAct Agent with Rich Streaming

**File**: `athos/src/athos/frameworks/langgraph/flows/react_agent.py` (enhanced)

```python
"""Enhanced LangGraph ReAct agent with rich streaming and LangGraph checkpointing."""

from typing import AsyncGenerator, Optional, List
import logging

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent
from langgraph.config import get_stream_writer

from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput, Artifact
from athos.models.enums import ExecutionMode
from athos.frameworks.langgraph.utils.translation import (
    to_langgraph_messages,
    from_langgraph_messages,
    build_langgraph_config,
)
from athos.frameworks.langgraph.utils.messages import HumanMessage

logger = logging.getLogger(__name__)


class LangGraphReactAgentFlow(BaseFlow):
    """
    ReAct agent with LangGraph checkpointing and rich streaming.

    Integration strategy:
    - LangGraph manages state via checkpointer with thread_id = session_id
    - We sync conversation history to FlowSession for consistency
    - We translate LangGraph events to FlowOutput
    - Custom events emitted via get_stream_writer()
    """

    name = "langgraph_react_agent"
    description = "ReAct agent with tool calling"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    def __init__(self):
        self._graph = None
        self._checkpointer = None
        self.model = None
        self.tools = []
        self.instructions = None

    async def initialize(self, config) -> None:
        """
        Initialize LangGraph with checkpointing.

        Uses SQLite checkpointer for persistence.
        Thread ID = our session_id.
        """
        from athos.frameworks.langgraph.factories import build_model, build_tools

        # LangGraph checkpointer
        self._checkpointer = SqliteSaver.from_conn_string(
            ":memory:"  # Or real DB path from config
        )

        # Build model and tools
        self.model = build_model(config.model)
        self.tools = build_tools(config.tools, config.mcp_servers)
        self.instructions = getattr(config, 'instructions', None)

        # Create LangGraph ReAct agent
        self._graph = create_react_agent(
            self.model,
            self.tools,
            prompt=self.instructions,
            checkpointer=self._checkpointer
        )

        logger.info(f"Initialized {self.name} with {len(self.tools)} tools")

    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute using LangGraph's state management."""

        # LangGraph config using our session_id as thread_id
        langgraph_config = build_langgraph_config(
            input.session.session_id,
            input.metadata
        )

        # Get current LangGraph state
        current_state = self._graph.get_state(langgraph_config)

        # Build messages (existing + new)
        messages = list(current_state.values.get("messages", []))
        messages.append(HumanMessage(input.message))

        # Execute
        result = await self._graph.ainvoke(
            {"messages": messages},
            config=langgraph_config
        )

        # Sync messages back to our session for consistency
        input.session.messages = from_langgraph_messages(result["messages"])

        # Extract response
        response = self._extract_last_ai_message(result["messages"])
        tools_used = self._extract_tools_used(result["messages"])

        return FlowOutput(
            content=response,
            metadata={"tools_used": tools_used}
        )

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """
        Stream with LangGraph custom events.

        Emits events for:
        - Thinking/reasoning steps
        - Tool calls (before execution)
        - Tool results (after execution)
        - Response chunks
        """

        langgraph_config = build_langgraph_config(
            input.session.session_id,
            input.metadata
        )

        # Build input state
        current_state = self._graph.get_state(langgraph_config)
        messages = list(current_state.values.get("messages", []))
        messages.append(HumanMessage(input.message))

        # Stream with custom mode
        accumulated_response = ""
        tools_used = []

        async for chunk in self._graph.astream(
            {"messages": messages},
            config=langgraph_config,
            stream_mode="custom"
        ):
            # Translate LangGraph custom events to our FlowOutput
            # (Custom events are emitted in the graph nodes via get_stream_writer())

            event_type = chunk.get("event_type")

            if event_type == "thinking":
                # Reasoning/planning step
                yield FlowOutput(
                    content=chunk["content"],
                    metadata={
                        "streaming": True,
                        "event_type": "thinking",
                        "status_message": "🤔 Thinking..."
                    }
                )

            elif event_type == "tool_call":
                # Tool is being called
                tool_name = chunk["tool_name"]
                tools_used.append(tool_name)

                yield FlowOutput(
                    content="",
                    metadata={
                        "streaming": True,
                        "event_type": "tool_call",
                        "tool_name": tool_name,
                        "status_message": f"🔧 Using tool: {tool_name}"
                    }
                )

            elif event_type == "tool_result":
                # Tool returned result
                yield FlowOutput(
                    content="",
                    metadata={
                        "streaming": True,
                        "event_type": "tool_result",
                        "tool_name": chunk["tool_name"],
                        "status_message": f"✓ Tool {chunk['tool_name']} completed"
                    }
                )

            elif event_type == "response_chunk":
                # Actual response being generated
                chunk_content = chunk["content"]
                accumulated_response += chunk_content

                yield FlowOutput(
                    content=chunk_content,
                    metadata={
                        "streaming": True,
                        "chunk": True,
                        "event_type": "response"
                    }
                )

        # Sync final state
        final_state = self._graph.get_state(langgraph_config)
        input.session.messages = from_langgraph_messages(final_state.values["messages"])

        # Final complete output
        yield FlowOutput(
            content=accumulated_response,
            metadata={
                "streaming": True,
                "chunk": False,
                "final": True,
                "tools_used": tools_used
            }
        )

    def _extract_last_ai_message(self, messages) -> str:
        """Extract last AI message content."""
        from langchain_core.messages import AIMessage

        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return msg.content

        return ""

    def _extract_tools_used(self, messages) -> List[str]:
        """Extract list of tools that were called."""
        from langchain_core.messages import ToolMessage

        tools = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                tools.append(msg.name)

        return list(set(tools))

    async def cleanup(self) -> None:
        """Close LangGraph checkpointer if needed."""
        if self._checkpointer and hasattr(self._checkpointer, 'close'):
            self._checkpointer.close()
```

**To emit custom events from the graph**, update agent implementation to use `get_stream_writer()`:

```python
# Example: In a custom agent node
def tool_calling_node(state):
    """Node that calls tools with streaming events."""
    from langgraph.config import get_stream_writer

    writer = get_stream_writer()

    for tool_call in state["messages"][-1].tool_calls:
        # Emit tool call event
        writer({
            "event_type": "tool_call",
            "tool_name": tool_call["name"],
            "tool_args": tool_call["args"]
        })

        # Execute tool
        result = tools[tool_call["name"]].invoke(tool_call["args"])

        # Emit result event
        writer({
            "event_type": "tool_result",
            "tool_name": tool_call["name"],
            "success": True
        })

    return state
```

#### Task 5.2: Create OpenWebUI Event Formatter

**File**: `athos/src/athos/integrations/openwebui/formatters.py`

```python
"""Formatting utilities for OpenWebUI events."""

from athos.models.flow import FlowOutput


def format_for_openwebui(output: FlowOutput) -> dict:
    """
    Format FlowOutput as OpenWebUI event.

    Supports:
    - Thinking blocks (reasoning_content)
    - Regular content
    - Status updates
    - Artifacts (images, files)
    """
    event_type = output.metadata.get("event_type")

    if event_type == "thinking":
        # OpenWebUI thinking block
        return {
            "choices": [{
                "delta": {
                    "reasoning_content": output.content
                },
                "finish_reason": None
            }]
        }

    elif event_type in ["tool_call", "tool_result"]:
        # Status event
        return {
            "event": {
                "type": "status",
                "data": {
                    "description": output.metadata.get("status_message", ""),
                    "done": False
                }
            }
        }

    elif output.metadata.get("chunk"):
        # Regular content chunk
        return {
            "choices": [{
                "delta": {
                    "content": output.content
                },
                "finish_reason": None
            }]
        }

    else:
        # Final output (render artifacts)
        content = output.content

        # Add artifacts as markdown
        for artifact in output.artifacts:
            if artifact.type == "image":
                content += f"\n\n![{artifact.display_name}]({artifact.path})"
            elif artifact.type == "file":
                content += f"\n\n📄 [{artifact.display_name}]({artifact.path})"
            elif artifact.type == "link":
                content += f"\n\n🔗 [{artifact.display_name}]({artifact.data})"

        return {
            "choices": [{
                "delta": {
                    "content": content
                },
                "finish_reason": "stop"
            }]
        }
```

Update Pipeline to use formatter:

```python
from athos.integrations.openwebui.formatters import format_for_openwebui

class Pipeline:
    def _execute_streaming(self, ...):
        def stream_generator():
            async def async_stream():
                async for output in self._runner.stream(...):
                    # Format for OpenWebUI
                    event = format_for_openwebui(output)
                    yield event

            # ... (bridge to sync) ...

        return stream_generator()
```

**Deliverables**:
- ✅ LangGraph flows with rich streaming
- ✅ LangGraph checkpointing integrated
- ✅ Custom event emission (thinking, tools, response)
- ✅ OpenWebUI formatter for all event types
- ✅ Thinking blocks visible in UI
- ✅ Tool call status updates
- ✅ Tests for streaming events and LangGraph integration

---

### Milestone 6: Production Hardening (Week 6-7)

**Goal**: Add reliability, observability, and operational features.

(Same as v2 plan: timeouts, metrics, health checks, comprehensive documentation)

**Deliverables**:
- ✅ Timeout and cancellation support
- ✅ Prometheus metrics
- ✅ Health check endpoint
- ✅ Comprehensive documentation
- ✅ Deployment examples (Docker Compose, K8s)
- ✅ Troubleshooting guide

---

## LangGraph Integration Summary

### How LangGraph Fits In

| LangGraph Feature | ATHOS Integration |
|-------------------|-------------------|
| **Checkpointing** | LangGraph's checkpointer with `thread_id = session_id` |
| **State** | LangGraph manages internally; we sync messages to `FlowSession` |
| **Messages** | Translate via `to_langgraph_messages()` / `from_langgraph_messages()` |
| **Streaming** | LangGraph's `stream_mode="custom"` → wrapped in `FlowOutput` |
| **Config** | Passed via `build_langgraph_config(session_id, metadata)` |
| **Tools** | Built via ATHOS factories, passed to LangGraph agent |

### Key Benefits

- ✅ **LangGraph handles persistence**: Uses its robust checkpointing system
- ✅ **Conversation continuity**: `thread_id = session_id` for stateful conversations
- ✅ **Framework-agnostic Runner**: FlowRunner doesn't know about LangGraph internals
- ✅ **Consistent interface**: All flows expose `FlowInput → FlowOutput`
- ✅ **Translation layer**: Clean utilities in `translation.py`

---

## Migration Path

### Phase 1: Foundation (M1-M2)
- New models package `athos/models/`
- FlowRunner created
- Compatibility shim for legacy flows
- LangGraph translation utilities
- One flow migrated as proof of concept
- **Existing flows continue to work**

### Phase 2: Integration (M3-M4)
- Basic Pipeline working
- Hook system operational
- CLI updated
- **Both old and new flows supported**

### Phase 3: Enhancement (M5)
- Streaming fully functional
- LangGraph flows with rich events
- **Gradual flow migration**

### Phase 4: Production (M6)
- Hardening complete
- All new features operational
- **Begin deprecating legacy interface**

### Phase 5: Cleanup (Future)
- Remove compatibility shim
- All flows using new interface
- **Clean, unified codebase**

---

## Testing Strategy

### Unit Tests
- Models (serialization, methods)
- SessionStore implementations
- FlowRunner execution and streaming
- Hook system (registration, firing, error isolation)
- LangGraph translation utilities
- Individual flows

### Integration Tests
- Pipeline pipe() method with mock flows
- Session persistence across requests
- Streaming event generation
- LangGraph checkpointing
- Error handling end-to-end

### End-to-End Tests
- Deploy OpenWebUI + Pipeline in Docker
- Send messages and verify responses
- Test streaming with real LangGraph flows
- Verify conversation history
- Check artifact rendering
- Verify LangGraph state persistence

### Performance Tests
- Concurrent request handling
- Timeout behavior under load
- Memory usage with long conversations
- Session store scalability
- LangGraph checkpointer performance

---

## Timeline Summary

| Milestone | Duration | Key Deliverables |
|-----------|----------|------------------|
| M1: Core Runtime | 1-2 weeks | Models package, SessionStore, BaseFlow, FlowRunner |
| M2: Migration & Compat | 1 week | Compatibility layer, translation utils, migrated flow, updated CLI |
| M3: Basic Pipeline | 1 week | Working Pipeline, basic streaming, deployment |
| M4: Hooks & Streaming | 1-1.5 weeks | Hook system, enhanced streaming, status events |
| M5: LangGraph Features | 1-1.5 weeks | Rich streaming, thinking blocks, tool visibility, checkpointing |
| M6: Production | 1 week | Timeout, metrics, health, docs |

**Total: 6.5-8 weeks** for complete implementation

---

## Success Criteria

### Milestone 1
- ✅ All models in `athos/models/` package
- ✅ Models serialize/deserialize correctly
- ✅ FlowRunner executes flows successfully
- ✅ Sessions persist state across requests
- ✅ Tests pass with 90%+ coverage

### Milestone 2
- ✅ Legacy flows work with new Runner
- ✅ LangGraph translation utilities work bidirectionally
- ✅ One flow fully migrated and tested
- ✅ CLI uses Runner successfully

### Milestone 3
- ✅ Pipeline deploys in Docker
- ✅ Can execute ATHOS flows from OpenWebUI
- ✅ Basic streaming works
- ✅ Session management functional

### Milestone 4
- ✅ Hooks fire at appropriate events
- ✅ Status events visible in OpenWebUI
- ✅ Error isolation prevents hook failures from crashing

### Milestone 5
- ✅ Thinking blocks render in OpenWebUI
- ✅ Tool calls visible as status updates
- ✅ LangGraph checkpointing preserves conversation state
- ✅ Streaming smooth and responsive

### Milestone 6
- ✅ Timeouts prevent runaway executions
- ✅ Metrics available for monitoring
- ✅ Health check returns accurate status
- ✅ Documentation complete and accurate

---

## Conclusion

This plan provides:

1. **Rich, Structured Interfaces**: `FlowInput`, `FlowOutput`, `FlowSession` enable advanced features
2. **Clean Package Structure**: Models in `athos/models/` with no circular dependencies
3. **Stateless Flows**: Pure functions that are testable and shareable
4. **External Session Management**: Pluggable persistence with clean separation
5. **LangGraph Integration**: Let LangGraph handle checkpointing, we coordinate and translate
6. **First-Class Streaming**: Built into interfaces, not bolted on
7. **Hook System**: Observability and extensibility without coupling
8. **Backward Compatibility**: Existing flows work during migration
9. **Production Ready**: Timeouts, metrics, health checks, comprehensive docs

The design cleanly separates concerns:
- **Models** = Data structures (no dependencies)
- **Interfaces** = Contracts (depend on models)
- **Flows** = Business logic (implement interfaces)
- **Runner** = Orchestration (uses models, interfaces, flows)
- **Pipeline** = Protocol translation (uses runner)

This architecture supports current needs (OpenWebUI) while enabling future integrations (CLI enhancement, SlackBot, Jupyter) with minimal changes. LangGraph integration is clean and leverages LangGraph's strengths while maintaining framework-agnostic abstractions.


###   Areas for Consideration & Minor Concerns:

1. SessionStore Implementation: The plan starts with an InMemorySessionStore, which is perfect for
   development. However, for a production OpenWebUI deployment, this will be a limitation (sessions will
   be lost on restart). The plan mentions Redis as a future option, but it would be beneficial to
   explicitly add a task in a later milestone (e.g., Milestone 4 or 5) to implement and test a persistent
    SessionStore (like Redis or a database-backed one).
2. Workspace Path in `FlowRunner`: The _get_workspace_path method hardcodes a default base path
   (/tmp/athos_workspace). While it can be overridden via the config, it might be safer to make
   workspace_path a required configuration key in AthosConfig to prevent accidental writes to a system
   temp directory if the config is missing. This forces the deployer to be explicit about where user data
   is stored.
3. Error Handling in Streaming: In the _execute_streaming method within the OpenWebUI Pipeline class, the
   try...except block wraps the entire generator. If an exception occurs mid-stream, it correctly yields
   an error message. However, it might be useful for the FlowRunner.stream() method itself to yield a
   final FlowOutput with an error payload, allowing the caller (Pipeline) to handle it more gracefully and
    consistently, rather than relying on a top-level try/except.
4. LangGraph Checkpointer: The LangGraphReactAgentFlow example initializes the SqliteSaver with
   ":memory:". This is great for testing, but the comment Or real DB path from config is key. It should
   be emphasized that for session persistence to work correctly across pipeline restarts, this needs to
   be a file path derived from the configuration. This should be a mandatory configuration item for
   persistent LangGraph flows.
5. Configuration for `athos-pipeline` service: In the docker-compose.yml, the environment variables
   CONFIG_PATH, DEFAULT_FLOW, etc., are hardcoded. These are correctly mapped to the Valves in the
   Pipeline class, which is good. It's just worth noting that any changes to these require a service
   restart, which is reasonable for this kind of configuration.
