# ATHOS OpenWebUI Pipelines Integration Plan (v2)

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
7. **Start Simple, Extend Later**: Begin with basic execution, add features incrementally
8. **Backward Compatible**: Existing flows work during migration

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

## Core Data Models

### FlowInput: Rich Input to Flows

```python
@dataclass
class FlowInput:
    """
    Rich input passed to flows.

    Provides everything a flow needs without coupling to interfaces.
    """
    message: str                    # User's message/query
    session: FlowSession            # Session state (history, workspace)
    mode: ExecutionMode             # SYNC, STREAMING, INTERACTIVE
    metadata: dict                  # Per-request extras
```

**Key Benefits**:
- **Single parameter**: Flows receive one structured input instead of many args
- **Extensible**: Add new fields without breaking existing flows
- **Testable**: Easy to create test inputs with controlled state

### FlowOutput: Structured Results

```python
@dataclass
class FlowOutput:
    """
    Structured output from flows.

    Supports text, artifacts (images/files), and metadata.
    """
    content: str                    # Primary text response
    artifacts: list[Artifact]       # Images, plots, files, links
    metadata: dict                  # Execution details (tokens, tools used, etc.)

@dataclass
class Artifact:
    """Something the flow produced beyond text."""
    type: str                       # "image", "file", "data", "link"
    path: Optional[str]             # For files/images
    data: Optional[Any]             # For inline data
    display_name: str
    metadata: dict
```

**Key Benefits**:
- **Structured artifacts**: Separate plots/files from text
- **Rich metadata**: Track tokens, tool calls, performance
- **OpenWebUI formatting**: Pipeline knows how to render artifacts

### FlowSession: External State Management

```python
@dataclass
class FlowSession:
    """
    Session state managed by Runner (not flows).

    Persists conversation history and custom state across invocations.
    """
    session_id: str
    user_id: str

    # Conversation history (framework-neutral)
    messages: list[dict]            # [{"role": "user", "content": "..."}, ...]

    # Workspace for files
    workspace: Path

    # Interface context
    interface: str                  # "openwebui", "cli", "slackbot"

    # Custom state (flows can store anything)
    state: dict

    # Metadata
    created_at: datetime
    updated_at: datetime
    metadata: dict
```

**Key Benefits**:
- **Flow-agnostic history**: Works with any framework
- **Workspace isolation**: Per-session file storage
- **Pluggable persistence**: In-memory, Redis, DB
- **Flows stay stateless**: State lives externally

### FlowResult: Execution Outcome

```python
@dataclass
class FlowResult:
    """
    Result of a flow execution via Runner.

    Wraps FlowOutput with execution metadata.
    """
    request_id: str                 # Unique request identifier
    success: bool                   # Did it succeed?
    output: Optional[FlowOutput]    # The actual output (if success)
    error: Optional[str]            # Error message (if failure)
    execution_time: float           # How long it took
    metadata: dict                  # Runner-level metadata
```

**Key Benefits**:
- **Success/failure clarity**: No ambiguity about errors
- **Request correlation**: Trace requests through logs
- **Performance tracking**: Built-in timing
- **Error formatting**: Consistent user-facing messages

## Enhanced BaseFlow Interface

```python
class ExecutionMode(str, Enum):
    """How the flow should be executed."""
    SYNC = "sync"                   # Single execute() call
    STREAMING = "streaming"         # Stream updates incrementally
    INTERACTIVE = "interactive"     # Multi-turn with interrupts (future)


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

    async def initialize(self, config: FlowConfig) -> None:
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

## Milestone Breakdown

### Milestone 1: Core Runtime Foundation (Week 1-2)

**Goal**: Establish the new runtime models and basic FlowRunner without breaking existing flows.

#### Task 1.1: Create Runtime Models

**File**: `athos/src/athos/runtime/models.py`

```python
# Models to create:
- ExecutionMode(Enum)
- FlowInput(dataclass)
- FlowOutput(dataclass)
- Artifact(dataclass)
- FlowSession(dataclass)
- FlowResult(dataclass)
- FlowRequest(dataclass) - internal to Runner
```

**Implementation Details**:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, AsyncGenerator
import uuid

class ExecutionMode(str, Enum):
    SYNC = "sync"
    STREAMING = "streaming"
    INTERACTIVE = "interactive"

@dataclass
class Artifact:
    """Artifact produced by a flow (image, file, data, link)."""
    type: str  # "image", "file", "data", "link"
    path: Optional[str] = None
    data: Optional[Any] = None
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
    """Structured output from a flow execution."""
    content: str
    artifacts: list[Artifact] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "metadata": self.metadata,
        }

@dataclass
class FlowSession:
    """Session state managed by Runner."""
    session_id: str
    user_id: str
    messages: list[dict] = field(default_factory=list)
    workspace: Path = field(default_factory=lambda: Path("/tmp"))
    interface: str = "unknown"
    state: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add message to history."""
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        self.updated_at = datetime.now()

    def get_history(self, limit: Optional[int] = None) -> list[dict]:
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

@dataclass
class FlowInput:
    """Rich input to flows."""
    message: str
    session: FlowSession
    mode: ExecutionMode = ExecutionMode.SYNC
    metadata: dict = field(default_factory=dict)

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
```

**Tests**: `tests/runtime/test_models.py`
- Serialization/deserialization
- FlowSession message management
- Artifact creation and metadata

#### Task 1.2: Create SessionStore Abstraction

**File**: `athos/src/athos/runtime/session_store.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
from athos.runtime.models import FlowSession

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

#### Task 1.3: Update BaseFlow Interface

**File**: `athos/src/athos/interfaces/base_flow.py`

```python
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional
from athos.runtime.models import FlowInput, FlowOutput, ExecutionMode

class BaseFlow(ABC):
    """Enhanced base flow interface with rich I/O."""

    # Class-level metadata
    name: str = "base_flow"
    description: str = "Base flow"
    supported_modes: list[ExecutionMode] = [ExecutionMode.SYNC]

    @abstractmethod
    async def execute(self, input: FlowInput) -> FlowOutput:
        """Execute flow and return structured output."""
        raise NotImplementedError

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Stream execution with intermediate updates."""
        # Default: execute once and yield
        result = await self.execute(input)
        yield result

    async def initialize(self, config: Any) -> None:
        """One-time initialization with config."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    def can_stream(self) -> bool:
        """Check if this flow supports streaming."""
        return ExecutionMode.STREAMING in self.supported_modes

    # DEPRECATED: Keep for backward compatibility during migration
    async def execute_legacy(self, input_data: str) -> Any:
        """
        Legacy execute method (DEPRECATED).

        Will be removed after all flows migrate to new interface.
        """
        # Shim to new interface
        from pathlib import Path
        from athos.runtime.models import FlowSession

        session = FlowSession(
            session_id="legacy",
            user_id="legacy",
            workspace=Path("/tmp"),
        )
        flow_input = FlowInput(
            message=input_data,
            session=session,
        )
        output = await self.execute(flow_input)
        return output.content
```

**Migration Strategy**:
1. Keep old `execute(str) -> Any` as `execute_legacy()` temporarily
2. Add new `execute(FlowInput) -> FlowOutput`
3. Flows can implement both during transition
4. Remove `execute_legacy()` in final phase

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
from athos.runtime.models import (
    FlowRequest, FlowResult, FlowInput, FlowOutput,
    FlowSession, ExecutionMode
)
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
    - Emit hooks for observability (future)
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
                interface="unknown",  # Set by caller
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
        base = Path(self.config.workspace_path or "/tmp/athos_workspace")
        return base / user_id / session_id
```

**Tests**: `tests/runtime/test_runner.py`
- Execute flow successfully
- Handle flow errors gracefully
- Session creation and reuse
- Flow caching
- Cleanup on shutdown

**Deliverables**:
- ✅ All runtime models defined
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

from athos.interfaces.base_flow import BaseFlow
from athos.runtime.models import FlowInput, FlowOutput

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
        if hasattr(self._legacy_flow, 'execute_legacy'):
            result = await self._legacy_flow.execute_legacy(input.message)
        else:
            result = await self._legacy_flow.execute(input.message)

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
```

**Update Runner** to auto-detect and adapt legacy flows:

```python
# In FlowRunner._get_flow()
async def _get_flow(self, flow_name: str) -> BaseFlow:
    if flow_name in self._flow_cache:
        return self._flow_cache[flow_name]

    flow = build_flow(flow_name, self.config)

    # Auto-detect legacy flows
    if not hasattr(flow, 'execute') or not _is_new_interface(flow):
        from athos.runtime.compat import LegacyFlowAdapter
        logger.warning(
            f"Flow '{flow_name}' uses legacy interface, adapting"
        )
        flow = LegacyFlowAdapter(flow)

    await flow.initialize(self.config.flows[flow_name])
    self._flow_cache[flow_name] = flow

    return flow

def _is_new_interface(flow: BaseFlow) -> bool:
    """Check if flow uses new FlowInput/FlowOutput interface."""
    import inspect
    sig = inspect.signature(flow.execute)
    params = list(sig.parameters.values())
    if len(params) != 1:
        return False

    # Check if parameter is annotated with FlowInput
    param_annotation = params[0].annotation
    return 'FlowInput' in str(param_annotation)
```

#### Task 2.2: Migrate LangGraph Chatbot Flow

**File**: `athos/src/athos/frameworks/langgraph/flows/chatbot.py` (refactored)

```python
"""Refactored LangGraph chatbot using new interface."""

from typing import Optional, AsyncGenerator
import logging

from athos.config.models import AthosConfig, BaseFlowConfig, ModelConfig
from athos.frameworks.langgraph.factories import build_model
from athos.interfaces.base_flow import BaseFlow
from athos.runtime.models import FlowInput, FlowOutput, ExecutionMode
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
    """

    name = "langgraph_chatbot"
    description = "Simple conversational chatbot using LangGraph"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    def __init__(self):
        self.model = None
        self.system_prompt = None

    async def initialize(self, config: BaseFlowConfig) -> None:
        """Load model once during initialization."""
        # Extract model config from AthosConfig
        # (This will be passed differently in production)
        from athos.runtime.builder import build_config
        full_config = build_config("config/config.yaml")  # TODO: pass properly

        model_cfg: ModelConfig = full_config.models[config.model]
        self.model = build_model(model_cfg)
        self.system_prompt = getattr(config, 'system_prompt', None)

        logger.info(f"Initialized {self.name} with model {model_cfg.model_id}")

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
                    "model": self.model.model_name if hasattr(self.model, 'model_name') else "unknown",
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
                    "model": self.model.model_name if hasattr(self.model, 'model_name') else "unknown",
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
            SystemMessage, HumanMessage, AIMessage
        )

        messages = []

        # System prompt
        if self.system_prompt:
            messages.append(SystemMessage(self.system_prompt))

        # History from session
        for msg in input.session.get_history():
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content))
            elif role == "assistant":
                messages.append(AIMessage(content))

        # Current message
        messages.append(HumanMessage(input.message))

        return messages

    async def cleanup(self) -> None:
        """No cleanup needed (model is lightweight)."""
        pass


# Register with new interface
register_flow(
    "langgraph_chatbot",
    # ... config class unchanged ...
)
```

**Key Improvements**:
- ✅ **Stateless**: No `self._history`, reads from `input.session`
- ✅ **Rich output**: Returns `FlowOutput` with metadata
- ✅ **Streaming**: Implements true streaming via `stream()`
- ✅ **Lifecycle**: Uses `initialize()` for one-time setup
- ✅ **Shareable**: Same instance can serve multiple sessions

#### Task 2.3: Update CLI to Use Runner

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
            metadata={"cli": True}
        )

        if result.success:
            print(result.output.content)

            # Show artifacts if any
            for artifact in result.output.artifacts:
                print(f"\n[Artifact: {artifact.display_name}]")
                if artifact.type == "file":
                    print(f"  Path: {artifact.path}")
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
from athos.runtime.models import FlowOutput


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
                    metadata={"interface": "openwebui"}
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
                    accumulated_output = None

                    async for output in self._runner.stream(
                        flow_name=self.valves.default_flow,
                        message=message,
                        session_id=session_id,
                        user_id=user_id,
                        metadata={"interface": "openwebui"}
                    ):
                        accumulated_output = output

                        # Yield chunks
                        if output.metadata.get("chunk"):
                            # Intermediate chunk
                            yield output.content
                        else:
                            # Final output
                            yield self._format_output(output)

                    # Clear status
                    yield self._create_status_event("", done=True)

                # Run async stream
                gen = async_stream()
                while True:
                    try:
                        chunk = loop.run_until_complete(gen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break

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
      - ATHOS_CONFIG_PATH=/app/config/config.yaml
      - ATHOS_WORKSPACE=/app/workspace

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

#### Task 4.1: Create Hook System

**File**: `athos/src/athos/runtime/hooks.py`

```python
"""Hook system for runtime observability and extensibility."""

import asyncio
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class HookEvent(str, Enum):
    """Hook event types."""
    BEFORE_EXECUTE = "before_execute"
    AFTER_SUCCESS = "after_success"
    AFTER_ERROR = "after_error"
    BEFORE_STREAM = "before_stream"
    OUTPUT_CHUNK = "output_chunk"
    AFTER_STREAM_COMPLETE = "after_stream_complete"
    FLOW_LOADED = "flow_loaded"
    SESSION_CREATED = "session_created"


@dataclass
class Hook:
    """A registered hook."""
    event: HookEvent
    callback: Callable
    priority: int = 0
    is_async: bool = True


class HookManager:
    """
    Manages hook registration and execution.

    Features:
    - Ordered execution by priority
    - Async and sync callback support
    - Error isolation (hooks don't crash flows)
    - Context passing to hooks
    """

    def __init__(self):
        self._hooks: Dict[HookEvent, List[Hook]] = {
            event: [] for event in HookEvent
        }

    def register(
        self,
        event: HookEvent,
        callback: Callable,
        priority: int = 0,
        is_async: bool = True,
    ) -> None:
        """
        Register a hook callback.

        Args:
            event: When to fire the hook
            callback: Function to call
            priority: Lower = earlier (default 0)
            is_async: Whether callback is async
        """
        hook = Hook(
            event=event,
            callback=callback,
            priority=priority,
            is_async=is_async,
        )

        self._hooks[event].append(hook)

        # Sort by priority
        self._hooks[event].sort(key=lambda h: h.priority)

        logger.debug(
            f"Registered hook for {event.value} "
            f"(priority={priority}, async={is_async})"
        )

    async def fire(self, event: HookEvent, **context) -> None:
        """
        Fire all hooks for an event.

        Args:
            event: Which event to fire
            **context: Context passed to hooks
        """
        hooks = self._hooks.get(event, [])

        if not hooks:
            return

        logger.debug(f"Firing {len(hooks)} hooks for {event.value}")

        for hook in hooks:
            try:
                if hook.is_async:
                    await hook.callback(**context)
                else:
                    # Run sync callback in executor
                    await asyncio.to_thread(hook.callback, **context)

            except Exception as e:
                # Isolate errors - don't let hooks crash flows
                logger.warning(
                    f"Hook {hook.callback.__name__} for {event.value} failed: {e}",
                    exc_info=True
                )

    def clear(self, event: Optional[HookEvent] = None) -> None:
        """Clear hooks for an event (or all events)."""
        if event:
            self._hooks[event].clear()
        else:
            for event in HookEvent:
                self._hooks[event].clear()
```

**Built-in Hooks** (`athos/src/athos/runtime/hooks/builtin.py`):

```python
"""Built-in hooks for common use cases."""

import logging
from athos.runtime.models import FlowResult, FlowOutput

logger = logging.getLogger(__name__)


# Logging hooks

async def log_execution_start(request, **kwargs):
    """Log when execution starts."""
    logger.info(
        f"Starting execution: flow={request.flow_name}, "
        f"user={request.user_id}, session={request.session_id}"
    )


async def log_execution_complete(result: FlowResult, **kwargs):
    """Log when execution completes."""
    logger.info(
        f"Execution complete: request_id={result.request_id}, "
        f"success={result.success}, time={result.execution_time:.2f}s"
    )


async def log_execution_error(result: FlowResult, exception: Exception, **kwargs):
    """Log execution errors."""
    logger.error(
        f"Execution failed: request_id={result.request_id}, "
        f"error={result.error}, exception={type(exception).__name__}"
    )


# Metrics hooks (Prometheus example)

class MetricsHook:
    """Prometheus metrics collection."""

    def __init__(self):
        try:
            from prometheus_client import Counter, Histogram

            self.request_counter = Counter(
                'athos_requests_total',
                'Total ATHOS requests',
                ['flow_name', 'success']
            )

            self.execution_time = Histogram(
                'athos_execution_seconds',
                'ATHOS execution time',
                ['flow_name']
            )

        except ImportError:
            logger.warning("prometheus_client not installed, metrics disabled")
            self.request_counter = None
            self.execution_time = None

    async def record_result(self, result: FlowResult, **kwargs):
        """Record metrics from result."""
        if not self.request_counter:
            return

        flow_name = result.metadata.get('flow_name', 'unknown')

        self.request_counter.labels(
            flow_name=flow_name,
            success=result.success
        ).inc()

        self.execution_time.labels(
            flow_name=flow_name
        ).observe(result.execution_time)


# Status event hook for OpenWebUI

class StatusEventHook:
    """
    Hook that captures status events for OpenWebUI streaming.

    Usage:
        hook = StatusEventHook()
        runner.hook_manager.register(HookEvent.OUTPUT_CHUNK, hook.on_chunk)

        # Later in Pipeline:
        for event in hook.get_events():
            yield event
    """

    def __init__(self):
        self._events = []

    async def on_chunk(self, output: FlowOutput, **kwargs):
        """Capture output chunks as status events."""
        if output.metadata.get('status_message'):
            self._events.append({
                "event": {
                    "type": "status",
                    "data": {
                        "description": output.metadata['status_message'],
                        "done": output.metadata.get('done', False),
                    }
                }
            })

    def get_events(self):
        """Get and clear captured events."""
        events = self._events.copy()
        self._events.clear()
        return events
```

#### Task 4.2: Integrate Hooks into FlowRunner

Update `FlowRunner` to use hooks:

```python
class FlowRunner:
    def __init__(
        self,
        config: AthosConfig,
        session_store: Optional[SessionStore] = None,
        hook_manager: Optional[HookManager] = None,  # NEW
    ):
        self.config = config
        self.session_store = session_store or InMemorySessionStore()
        self.hook_manager = hook_manager or HookManager()  # NEW

        # Register built-in hooks
        from athos.runtime.hooks.builtin import (
            log_execution_start,
            log_execution_complete,
            log_execution_error,
        )

        self.hook_manager.register(
            HookEvent.BEFORE_EXECUTE,
            log_execution_start
        )
        self.hook_manager.register(
            HookEvent.AFTER_SUCCESS,
            log_execution_complete
        )
        self.hook_manager.register(
            HookEvent.AFTER_ERROR,
            log_execution_error
        )

        self._flow_cache: Dict[str, BaseFlow] = {}

    async def execute(self, ...):
        request = FlowRequest(...)

        # Fire before hook
        await self.hook_manager.fire(
            HookEvent.BEFORE_EXECUTE,
            request=request
        )

        try:
            # ... execute flow ...

            result = FlowResult(...)

            # Fire success hook
            await self.hook_manager.fire(
                HookEvent.AFTER_SUCCESS,
                result=result
            )

            return result

        except Exception as e:
            result = FlowResult(...)

            # Fire error hook
            await self.hook_manager.fire(
                HookEvent.AFTER_ERROR,
                result=result,
                exception=e
            )

            return result

    async def stream(self, ...):
        request = FlowRequest(...)

        # Fire before stream hook
        await self.hook_manager.fire(
            HookEvent.BEFORE_STREAM,
            request=request
        )

        try:
            async for output in flow.stream(flow_input):
                # Fire chunk hook
                await self.hook_manager.fire(
                    HookEvent.OUTPUT_CHUNK,
                    output=output
                )

                yield output

            # Fire completion hook
            await self.hook_manager.fire(
                HookEvent.AFTER_STREAM_COMPLETE,
                request=request
            )

        except Exception as e:
            await self.hook_manager.fire(
                HookEvent.AFTER_ERROR,
                exception=e
            )
            raise
```

#### Task 4.3: Enhance Pipeline with Status Events

Update Pipeline to use hooks for status events:

```python
class Pipeline:
    def _execute_streaming(self, message, user_id, session_id):
        """Enhanced streaming with status events."""

        def stream_generator():
            loop = asyncio.new_event_loop()

            try:
                # Create hook for status events
                from athos.runtime.hooks.builtin import StatusEventHook
                status_hook = StatusEventHook()

                # Register hook
                self._runner.hook_manager.register(
                    HookEvent.OUTPUT_CHUNK,
                    status_hook.on_chunk
                )

                # Initial status
                yield self._create_status_event("Initializing...", False)

                async def async_stream():
                    async for output in self._runner.stream(...):
                        # Yield any status events captured by hook
                        for event in status_hook.get_events():
                            yield event

                        # Yield content
                        if output.metadata.get("chunk"):
                            yield output.content
                        else:
                            yield self._format_output(output)

                # Run stream
                # ... (bridge async to sync) ...

                # Final status
                yield self._create_status_event("", True)

            finally:
                loop.close()

        return stream_generator()
```

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

#### Task 5.1: Enhance LangGraph Flows with Rich Streaming

**File**: `athos/src/athos/frameworks/langgraph/flows/react_agent.py` (enhanced)

```python
"""Enhanced LangGraph ReAct agent with rich streaming."""

from typing import AsyncGenerator
from langgraph.config import get_stream_writer

from athos.runtime.models import FlowInput, FlowOutput, Artifact, ExecutionMode
from athos.interfaces.base_flow import BaseFlow


class LangGraphReactAgentFlow(BaseFlow):
    """ReAct agent with rich streaming support."""

    name = "langgraph_react_agent"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    # ... (initialization code) ...

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """
        Stream with rich events: thinking, tool calls, responses.

        Uses LangGraph's get_stream_writer() to emit custom events.
        """
        await self._ensure_mcp_tools_loaded()
        await self._ensure_graph_built()

        # Build state
        state = {
            "messages": self._build_messages(input),
            # Inject stream writer context
            "_stream_writer": get_stream_writer()
        }

        accumulated_response = ""
        tool_calls_made = []

        async for chunk in self._graph.astream(state, stream_mode="custom"):
            # LangGraph custom events
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
                tool_calls_made.append(tool_name)

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

        # Final complete output
        yield FlowOutput(
            content=accumulated_response,
            metadata={
                "streaming": True,
                "chunk": False,
                "final": True,
                "tools_used": tool_calls_made
            }
        )
```

To emit these custom events from within the graph, update the agent implementation:

```python
# In the agent's tool-calling node:
def call_tools(state):
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

#### Task 5.2: Update Pipeline to Render Thinking Blocks

**File**: `athos/src/athos/integrations/openwebui/formatters.py` (new)

```python
"""Formatting utilities for OpenWebUI events."""

from athos.runtime.models import FlowOutput


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
- ✅ Custom event emission (thinking, tools, response)
- ✅ OpenWebUI formatter for all event types
- ✅ Thinking blocks visible in UI
- ✅ Tool call status updates
- ✅ Tests for streaming events

---

### Milestone 6: Production Hardening (Week 6-7)

**Goal**: Add reliability, observability, and operational features.

#### Task 6.1: Timeout and Cancellation

Update FlowRunner:

```python
import asyncio

class FlowRunner:
    async def execute(self, ..., timeout: Optional[float] = None):
        """Execute with optional timeout."""
        if timeout is None:
            timeout = self.config.get('default_timeout', 300)

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_internal(...),
                timeout=timeout
            )
            return result

        except asyncio.TimeoutError:
            logger.error(f"Execution timed out after {timeout}s")
            return FlowResult(
                request_id=request.request_id,
                success=False,
                output=None,
                error=f"Execution timed out after {timeout}s",
                execution_time=timeout,
                metadata={"timeout": True}
            )
```

#### Task 6.2: Metrics Endpoint

**File**: `athos/src/athos/integrations/openwebui/metrics.py`

```python
"""Prometheus metrics endpoint for Pipeline."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
request_counter = Counter(
    'athos_requests_total',
    'Total requests',
    ['flow', 'status']
)

execution_time = Histogram(
    'athos_execution_seconds',
    'Execution time',
    ['flow']
)

active_requests = Gauge(
    'athos_active_requests',
    'Currently active requests'
)


def get_metrics() -> bytes:
    """Get Prometheus metrics."""
    return generate_latest()
```

Add `/metrics` endpoint to Pipeline (if using FastAPI wrapper).

#### Task 6.3: Health Check

```python
class Pipeline:
    async def health_check(self) -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy" if self._initialized else "initializing",
            "flows_cached": len(self._runner._flow_cache),
            "sessions_active": len(self._runner.session_store._sessions),
        }
```

#### Task 6.4: Documentation

**File**: `docs/openwebui_integration.md`

```markdown
# ATHOS OpenWebUI Integration Guide

## Architecture

[Diagram and explanation]

## Deployment

### Docker Compose
[Instructions]

### Kubernetes
[Helm chart and instructions]

## Configuration

### Valves
[All valve options explained]

### ATHOS Config
[How to configure flows, models, MCPs]

## Troubleshooting

### Common Issues
[Known problems and solutions]

### Debugging
[How to enable debug logging]

### Performance Tuning
[Optimization tips]

## Monitoring

### Metrics
[Prometheus metrics available]

### Logging
[Log format and levels]
```

**Deliverables**:
- ✅ Timeout and cancellation support
- ✅ Prometheus metrics
- ✅ Health check endpoint
- ✅ Comprehensive documentation
- ✅ Deployment examples (Docker Compose, K8s)
- ✅ Troubleshooting guide

---

## Migration Path

### Phase 1: Foundation (M1-M2)
- New runtime models added
- FlowRunner created
- Compatibility shim for legacy flows
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
- Runtime models (serialization, methods)
- SessionStore implementations
- FlowRunner execution and streaming
- Hook system (registration, firing, error isolation)
- Individual flows

### Integration Tests
- Pipeline pipe() method with mock flows
- Session persistence across requests
- Streaming event generation
- Error handling end-to-end

### End-to-End Tests
- Deploy OpenWebUI + Pipeline in Docker
- Send messages and verify responses
- Test streaming with real LangGraph flows
- Verify conversation history
- Check artifact rendering

### Performance Tests
- Concurrent request handling
- Timeout behavior under load
- Memory usage with long conversations
- Session store scalability

---

## Timeline Summary

| Milestone | Duration | Key Deliverables |
|-----------|----------|------------------|
| M1: Core Runtime | 1-2 weeks | Models, SessionStore, BaseFlow updates, FlowRunner |
| M2: Migration & Compat | 1 week | Compatibility layer, one migrated flow, updated CLI |
| M3: Basic Pipeline | 1 week | Working Pipeline, basic streaming, deployment |
| M4: Hooks & Streaming | 1-1.5 weeks | Hook system, enhanced streaming, status events |
| M5: LangGraph Features | 1-1.5 weeks | Rich streaming, thinking blocks, tool visibility |
| M6: Production | 1 week | Timeout, metrics, health, docs |

**Total: 6.5-8 weeks** for complete implementation

---

## Success Criteria

### Milestone 1
- ✅ All models serialize/deserialize correctly
- ✅ FlowRunner executes flows successfully
- ✅ Sessions persist state across requests
- ✅ Tests pass with 90%+ coverage

### Milestone 2
- ✅ Legacy flows work with new Runner
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
- ✅ Streaming smooth and responsive

### Milestone 6
- ✅ Timeouts prevent runaway executions
- ✅ Metrics available for monitoring
- ✅ Health check returns accurate status
- ✅ Documentation complete and accurate

---

## Conclusion

This redesigned plan provides:

1. **Rich, Structured Interfaces**: `FlowInput`, `FlowOutput`, `FlowSession` enable advanced features
2. **Stateless Flows**: Pure functions that are testable and shareable
3. **External Session Management**: Pluggable persistence with clean separation
4. **First-Class Streaming**: Built into interfaces, not bolted on
5. **Hook System**: Observability and extensibility without coupling
6. **Backward Compatibility**: Existing flows work during migration
7. **Production Ready**: Timeouts, metrics, health checks, comprehensive docs

The design cleanly separates concerns:
- **Flows** = Business logic
- **Runner** = Orchestration
- **Session** = State persistence
- **Pipeline** = Protocol translation

This architecture supports current needs (OpenWebUI) while enabling future integrations (CLI enhancement, SlackBot, Jupyter) with minimal changes.
