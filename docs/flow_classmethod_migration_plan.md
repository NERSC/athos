# Flow Classmethod Factory Migration Plan

**Status:** Planning
**Created:** 2025-10-21
**Goal:** Migrate ATHOS flows from factory-function + initialize pattern to classmethod factory pattern with constructor dependency injection

## Executive Summary

This document outlines the migration from the current two-phase flow initialization pattern to a cleaner classmethod factory pattern that eliminates uninitialized state and provides better type safety.

### Current Problems
- **Uninitialized state window**: Flows exist in invalid state between construction and `initialize()`
- **Optional types everywhere**: Need `Optional[Model]` and defensive `if self.model is None` checks
- **Split responsibility**: Factory constructs, FlowRunner initializes (unclear ownership)
- **Potential misuse**: Direct construction creates unusable flows

### Solution
- **Classmethod factories**: `@classmethod async def create()` builds dependencies and calls constructor
- **Fat constructors**: Constructor takes all dependencies, flow valid immediately after construction
- **Class metadata**: `name`, `config_class`, `framework` as class attributes enable simple registration
- **No uninitialized state**: Type system guarantees flows are always ready to use

### Migration Strategy
Four-phase incremental migration maintaining backward compatibility at each step.

---

## Design Decisions

### 1. Classmethod Factory Pattern

**Pattern:**
```python
class MyFlow(BaseFlow):
    @classmethod
    async def create(
        cls,
        flow_config: MyFlowConfig,
        athos_config: AthosConfig
    ) -> MyFlow:
        # Build all dependencies
        model = build_model(athos_config.models[flow_config.model])

        # Call constructor with everything it needs
        return cls(model=model, config=athos_config)
```

**Rationale:**
- ✅ Discoverability - factory is on the class itself
- ✅ Encapsulation - everything about the flow in one place
- ✅ Enforcement - `@abstractmethod` ensures implementation
- ✅ Idiomatic - standard Python pattern (datetime.fromisoformat, etc.)

### 2. Constructor Dependency Injection

**Pattern:**
```python
class MyFlow(BaseFlow):
    def __init__(self, model: BaseLanguageModel, config: AthosConfig):
        self.model = model  # ✅ Required, not Optional[BaseLanguageModel]
        self.config = config
```

**Rationale:**
- ✅ No uninitialized state - flow valid immediately
- ✅ Type safety - no Optional[] types needed
- ✅ No defensive checks - can safely use self.model
- ✅ Testability - easy to inject mocks

### 3. Class Metadata for Registration

**Pattern:**
```python
class MyFlow(BaseFlow):
    name = "my_flow"
    config_class = MyFlowConfig
    framework = ToolFramework.LANGGRAPH
    description = "My flow description"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

# Simple registration
register_flow(MyFlow)
```

**Rationale:**
- ✅ Single source of truth - metadata with the class
- ✅ Simple registration - one argument instead of four
- ✅ Self-documenting - clear what each flow needs
- ✅ Type-safe - ClassVar annotations

### 4. Decorator Order

**Pattern:**
```python
@classmethod
@abstractmethod
async def create(cls, ...) -> Self:
    ...
```

**Note:** Order matters! `@classmethod` first (outermost), then `@abstractmethod` (innermost).

---

## Phase 1: Dual-Interface Foundation

**Goal:** Add support for new pattern while maintaining full backward compatibility

**Status:** Not Started
**Estimated Effort:** 2-3 days
**Risk:** 🟢 Low - additive only, no breaking changes

### 1.1 Update BaseFlow Interface

**File:** `src/athos/interfaces/base_flow.py`

**Changes:**
```python
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, ClassVar, Type
from typing_extensions import Self  # Python 3.11+, or use TypeVar

from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput, FlowOutput
from athos.config.models import AthosConfig, BaseFlowConfig, ToolFramework


class BaseFlow(ABC):
    """Enhanced base interface for all flow implementations."""

    # ===== Class-level metadata (required for new pattern) =====
    name: ClassVar[str]
    """Unique flow identifier used in registry and config"""

    description: ClassVar[str] = ""
    """Human-readable description of what this flow does"""

    config_class: ClassVar[Type[BaseFlowConfig]]
    """Pydantic config class for this flow's configuration"""

    framework: ClassVar[ToolFramework]
    """Framework this flow uses (SMOLAGENTS, LANGGRAPH, etc.)"""

    supported_modes: ClassVar[list[ExecutionMode]] = [ExecutionMode.SYNC]
    """Execution modes this flow supports"""

    # ===== Primary construction method (NEW PATTERN) =====
    @classmethod
    @abstractmethod
    async def create(
        cls,
        flow_config: BaseFlowConfig,
        athos_config: AthosConfig
    ) -> Self:
        """
        Create and fully initialize a flow instance.

        This is the primary way to construct flows in production.
        Subclasses must:
        1. Build all dependencies (models, tools, MCP clients)
        2. Call constructor with all required arguments
        3. Return a fully-initialized, ready-to-use flow

        Args:
            flow_config: Flow-specific configuration
            athos_config: Full ATHOS configuration

        Returns:
            Fully initialized flow instance
        """
        raise NotImplementedError(
            f"{cls.__name__} must implement create() classmethod"
        )

    # ===== Core execution interface =====
    @abstractmethod
    async def execute(self, input: FlowInput) -> FlowOutput:
        """
        Execute the flow once and return structured output.

        Args:
            input: FlowInput containing message, session, mode, metadata

        Returns:
            FlowOutput with content, artifacts, metadata
        """
        raise NotImplementedError

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """
        Stream execution with intermediate updates.

        Default implementation falls back to execute().
        Override for true streaming support.

        Args:
            input: FlowInput containing message, session, mode, metadata

        Yields:
            FlowOutput chunks (intermediate and final)
        """
        result = await self.execute(input)
        yield result

    # ===== Lifecycle management =====
    async def initialize(self, config: Any) -> None:
        """
        [DEPRECATED] One-time initialization for expensive resources.

        This method is deprecated in favor of the create() classmethod.
        New flows should not implement this - all setup should happen
        in create() before calling the constructor.

        Will be removed in a future version.
        """
        pass  # Default no-op for new flows

    async def cleanup(self) -> None:
        """
        Release any resources held by the flow instance.

        Called by FlowRunner during shutdown. Override if your flow
        manages resources like MCP connections, file handles, etc.
        """
        pass

    # ===== Capability detection =====
    def can_stream(self) -> bool:
        """Return whether this flow supports streaming execution."""
        return ExecutionMode.STREAMING in self.supported_modes
```

**Validation:**
- Add docstrings explaining new vs deprecated patterns
- Mark `initialize()` as deprecated
- Use `ClassVar` to prevent instance attribute conflicts

### 1.2 Update Registry to Support Both Patterns

**File:** `src/athos/registry/flow_registry.py`

**Changes:**
```python
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type, Union, overload
import inspect

from athos.interfaces.base_flow import BaseFlow
from athos.config.models import BaseFlowConfig, AthosConfig, ToolFramework

# ===== Type definitions =====
# Old pattern: standalone factory function
FlowFactory = Callable[[BaseFlowConfig, AthosConfig], BaseFlow]

# New pattern: flow class with create() classmethod
FlowClass = Type[BaseFlow]

# Union of both patterns
FlowCreator = Union[FlowFactory, FlowClass]


@dataclass(frozen=True)
class FlowRegistration:
    """Metadata stored for each registered flow type."""

    config_cls: Type[BaseFlowConfig]
    creator: FlowCreator  # ✅ Can be factory function OR flow class
    framework: ToolFramework


FLOW_REGISTRY: Dict[str, FlowRegistration] = {}


# ===== Registration function with overloads =====
@overload
def register_flow(flow_class: FlowClass) -> None:
    """Register a flow using class metadata (new pattern)."""
    ...


@overload
def register_flow(
    flow_type: str,
    config_cls: Type[BaseFlowConfig],
    creator: FlowCreator,
    *,
    framework: ToolFramework,
) -> None:
    """Register a flow with explicit arguments (legacy pattern)."""
    ...


def register_flow(
    flow_class_or_type: Union[FlowClass, str],
    config_cls: Optional[Type[BaseFlowConfig]] = None,
    creator: Optional[FlowCreator] = None,
    *,
    framework: Optional[ToolFramework] = None,
) -> None:
    """
    Register a flow type with the runtime.

    Supports two patterns:

    NEW PATTERN (recommended):
        @register_flow
        class MyFlow(BaseFlow):
            name = "my_flow"
            config_class = MyFlowConfig
            framework = ToolFramework.LANGGRAPH
            ...

        # Or without decorator:
        register_flow(MyFlow)

    LEGACY PATTERN (deprecated):
        register_flow(
            "my_flow",
            MyFlowConfig,
            create_my_flow_factory,
            framework=ToolFramework.LANGGRAPH
        )
    """

    # ===== NEW PATTERN: Single class argument =====
    if isinstance(flow_class_or_type, type) and issubclass(flow_class_or_type, BaseFlow):
        flow_class = flow_class_or_type

        # Validate required class metadata
        missing = []
        if not hasattr(flow_class, 'name') or not flow_class.name:
            missing.append('name')
        if not hasattr(flow_class, 'config_class') or not flow_class.config_class:
            missing.append('config_class')
        if not hasattr(flow_class, 'framework') or not flow_class.framework:
            missing.append('framework')

        if missing:
            raise ValueError(
                f"{flow_class.__name__} missing required class attributes: {', '.join(missing)}\n"
                f"New pattern flows must define: name, config_class, framework"
            )

        # Validate create() method exists
        if not hasattr(flow_class, 'create'):
            raise ValueError(
                f"{flow_class.__name__} missing create() classmethod.\n"
                f"New pattern flows must implement: @classmethod async def create(...)"
            )

        FLOW_REGISTRY[flow_class.name] = FlowRegistration(
            config_cls=flow_class.config_class,
            creator=flow_class,
            framework=flow_class.framework,
        )
        return

    # ===== LEGACY PATTERN: Multiple arguments =====
    if not isinstance(flow_class_or_type, str):
        raise TypeError(
            f"First argument must be a BaseFlow subclass or flow type string, "
            f"got {type(flow_class_or_type)}"
        )

    if config_cls is None or creator is None or framework is None:
        raise ValueError(
            "Legacy pattern requires all arguments: "
            "register_flow(flow_type, config_cls, creator, framework=...)"
        )

    flow_type = flow_class_or_type
    FLOW_REGISTRY[flow_type] = FlowRegistration(
        config_cls=config_cls,
        creator=creator,
        framework=framework,
    )


def register_flow_type(flow_class: FlowClass) -> FlowClass:
    """
    Decorator to auto-register a flow class.

    Usage:
        @register_flow_type
        class MyFlow(BaseFlow):
            name = "my_flow"
            config_class = MyFlowConfig
            framework = ToolFramework.LANGGRAPH
            ...

    The decorator returns the class unchanged, so it can be imported normally.
    """
    register_flow(flow_class)
    return flow_class


def get_available_flow_types() -> Dict[str, Type[BaseFlowConfig]]:
    """Get all available flow types and their config classes."""
    return {
        flow_type: registration.config_cls
        for flow_type, registration in FLOW_REGISTRY.items()
    }


def is_flow_type_registered(flow_type: str) -> bool:
    """Check if a flow type is registered."""
    return flow_type in FLOW_REGISTRY


def get_flow_registration(flow_type: str) -> Optional[FlowRegistration]:
    """Get registration metadata for a flow type."""
    return FLOW_REGISTRY.get(flow_type)
```

**Validation:**
- Type hints with overloads for IDE support
- Clear error messages for missing metadata
- Decorator variant for convenience

### 1.3 Update build_flow() to Handle Both Patterns

**File:** `src/athos/runtime/builder.py`

**Changes:**
```python
"""Runtime helpers to construct and execute flows."""

from typing import Any, Dict, Optional
import logging
import inspect

from athos.config import AthosConfig, ConfigLoader
from athos.interfaces.base_flow import BaseFlow
from athos.registry.flow_registry import FLOW_REGISTRY
from athos.utils.logging_utils import configure_logging
from athos.utils.workspace import get_workspace

logger = logging.getLogger(__name__)


async def build_flow(flow_name: str, config: AthosConfig) -> BaseFlow:
    """
    Construct a flow instance from configuration.

    Supports both new (classmethod create) and legacy (factory function) patterns.

    Args:
        flow_name: Name of the flow from config.flows
        config: Full ATHOS configuration

    Returns:
        Flow instance (fully initialized if using new pattern)

    Raises:
        ValueError: If flow_name not found or flow type not registered
    """
    if flow_name not in config.flows:
        raise ValueError(f"Unknown flow: {flow_name}")

    flow_cfg = config.flows[flow_name]
    registration = FLOW_REGISTRY.get(flow_cfg.type)
    if not registration:
        raise ValueError(f"Unknown flow type: {flow_cfg.type}")

    config_cls = registration.config_cls
    creator = registration.creator

    # Validate config type
    if not isinstance(flow_cfg, config_cls):
        raise TypeError(
            f"Flow '{flow_name}' config has type {type(flow_cfg).__name__} "
            f"but expected {config_cls.__name__}"
        )

    # ===== NEW PATTERN: Class with create() classmethod =====
    if inspect.isclass(creator) and hasattr(creator, 'create'):
        logger.debug(
            "Building flow '%s' using new pattern (create classmethod)",
            flow_name
        )
        flow = await creator.create(flow_cfg, config)

        # Mark that this flow was created via classmethod
        # (FlowRunner uses this to skip calling initialize)
        object.__setattr__(flow, '_created_via_classmethod', True)

        logger.debug(
            "Flow '%s' built and initialized via create()",
            flow_name
        )
        return flow

    # ===== LEGACY PATTERN: Factory function =====
    logger.debug(
        "Building flow '%s' using legacy pattern (factory function)",
        flow_name
    )

    # Factory might be sync or async
    result = creator(flow_cfg, config)
    if inspect.isawaitable(result):
        flow = await result
    else:
        flow = result

    logger.debug(
        "Flow '%s' built via factory (will need initialize() call)",
        flow_name
    )
    return flow


async def create_flows(config: AthosConfig) -> Dict[str, BaseFlow]:
    """
    Create all flows defined in the configuration.

    Note: Legacy pattern flows will need initialize() called separately.
    """
    flows = {}
    for name in config.flows:
        flows[name] = await build_flow(name, config)
    return flows


def build_config(config_path: str, overrides: Optional[Dict[str, Any]] = None) -> AthosConfig:
    """Load configuration from disk, apply overrides and logging configuration."""
    config = ConfigLoader.load_config(config_path, overrides)
    workspace = get_workspace(config)
    try:
        object.__setattr__(config, "workspace_path", workspace)
    except Exception:
        pass
    if config.logging_config is not None:
        configure_logging(config.logging_config)
    return config
```

**Key Points:**
- Detect pattern by checking if creator is a class with `create()` method
- Set `_created_via_classmethod` flag for FlowRunner
- Support both sync and async factories (legacy compatibility)

### 1.4 Update FlowRunner to Handle Both Patterns

**File:** `src/athos/runtime/runner.py`

**Changes:**
```python
async def _get_flow(self, flow_name: str) -> BaseFlow:
    """
    Return a cached flow instance or build a new one.

    Handles both new pattern (classmethod create) and legacy pattern
    (factory + initialize) flows transparently.
    """

    if flow_name in self._flow_cache:
        return self._flow_cache[flow_name]

    if flow_name not in self.config.flows:
        raise ValueError(f"Unknown flow: {flow_name}")

    flow_config = self.config.flows[flow_name]

    # Build flow using appropriate pattern
    logger.debug("Loading flow '%s'", flow_name)
    flow = await build_flow(flow_name, self.config)

    # Apply legacy adapter if needed
    if not is_new_interface(flow):
        logger.warning(
            "Flow '%s' uses legacy interface (str -> str); applying compatibility adapter",
            flow_name,
        )
        flow = LegacyFlowAdapter(flow)

    # Only call initialize() for legacy pattern flows
    # (new pattern flows are already initialized by create())
    created_via_classmethod = getattr(flow, '_created_via_classmethod', False)

    if not created_via_classmethod:
        logger.debug(
            "Flow '%s' built via legacy pattern; calling initialize()",
            flow_name
        )
        await flow.initialize(flow_config)
    else:
        logger.debug(
            "Flow '%s' already initialized via create() classmethod",
            flow_name
        )

    self._flow_cache[flow_name] = flow
    logger.info("Flow '%s' loaded and cached", flow_name)
    return flow
```

**Key Points:**
- Check `_created_via_classmethod` flag to decide whether to call `initialize()`
- Legacy flows still work with adapter + initialize
- New flows skip initialize (already done in create)

### 1.5 Testing Requirements

**Test File:** `tests/runtime/test_dual_interface.py`

**Test Cases:**
1. ✅ New pattern flow with create() registers correctly
2. ✅ Legacy pattern flow with factory function still works
3. ✅ New pattern flow builds without calling initialize()
4. ✅ Legacy pattern flow builds and gets initialize() called
5. ✅ Registration validation catches missing class metadata
6. ✅ Registration validation catches missing create() method
7. ✅ Both patterns work through FlowRunner.execute()
8. ✅ Decorator pattern works (@register_flow_type)

**Example Test:**
```python
import pytest
from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.registry.flow_registry import register_flow
from athos.runtime.builder import build_flow
from athos.config.models import AthosConfig, BaseFlowConfig, ToolFramework


class NewPatternFlowConfig(BaseFlowConfig):
    type: str = "new_pattern"


class NewPatternFlow(BaseFlow):
    name = "new_pattern"
    config_class = NewPatternFlowConfig
    framework = ToolFramework.LANGGRAPH

    def __init__(self, value: str):
        self.value = value

    @classmethod
    async def create(cls, flow_config, athos_config):
        return cls(value="initialized")

    async def execute(self, input: FlowInput) -> FlowOutput:
        return FlowOutput(content=self.value)


@pytest.mark.asyncio
async def test_new_pattern_flow_registration():
    """Test that new pattern flow registers and builds correctly."""
    # Register
    register_flow(NewPatternFlow)

    # Build config
    config = AthosConfig(
        flows={"test": NewPatternFlowConfig(type="new_pattern")},
        models={},
        mcp_servers={},
        tools={}
    )

    # Build flow
    flow = await build_flow("test", config)

    # Should be initialized
    assert hasattr(flow, '_created_via_classmethod')
    assert flow._created_via_classmethod is True
    assert flow.value == "initialized"
```

### 1.6 Documentation Updates

**Files to update:**
- `CLAUDE.md` - Document both patterns, recommend new pattern
- `docs/athos_openwebui_integration_status.md` - Mark Phase 1 complete
- `README.md` - Update flow creation examples

### 1.7 Success Criteria

- [ ] All existing tests pass
- [ ] New dual-interface tests pass
- [ ] Both LangGraph flows work (currently using old pattern)
- [ ] Both SmolAgents flows work (currently using legacy interface + old pattern)
- [ ] No breaking changes to existing code
- [ ] Documentation explains both patterns

---

## Phase 2: Migrate LangGraph Flows

**Goal:** Convert LangGraph chatbot and react_agent to new pattern as reference implementations

**Status:** Not Started
**Estimated Effort:** 1-2 days
**Risk:** 🟡 Medium - changing working code

**Dependencies:** Phase 1 complete

### 2.1 Migrate LangGraph Chatbot

**File:** `src/athos/frameworks/langgraph/flows/chatbot.py`

**Changes:**

**Step 1: Add class metadata**
```python
class LangGraphChatbotFlow(BaseLangGraphFlow):
    """Chatbot flow that produces structured outputs and supports streaming."""

    # ===== Class metadata =====
    name = "langgraph_chatbot"
    description = "Simple conversational chatbot using LangGraph"
    config_class = LangGraphChatbotFlowConfig  # Defined at bottom of file
    framework = ToolFramework.LANGGRAPH
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]
```

**Step 2: Update constructor to take dependencies**
```python
def __init__(
    self,
    model: "BaseLanguageModel",  # ✅ Required, not Optional
    system_prompt: Optional[str],
    initial_history: List[BaseMessage],
    full_config: AthosConfig
):
    """
    Construct a chatbot flow with all dependencies.

    Note: Use the create() classmethod in production.
    This constructor is public to support testing with mocks.

    Args:
        model: LangChain chat model (required)
        system_prompt: Optional system prompt
        initial_history: Pre-seeded conversation messages
        full_config: Full ATHOS configuration
    """
    super().__init__(full_config)
    self.model = model  # ✅ No longer Optional
    self.system_prompt = system_prompt
    self._initial_history = initial_history
```

**Step 3: Implement create() classmethod**
```python
@classmethod
async def create(
    cls,
    flow_config: LangGraphChatbotFlowConfig,
    athos_config: AthosConfig
) -> LangGraphChatbotFlow:
    """
    Create and fully initialize a chatbot flow.

    Builds the LangChain model and constructs the flow instance.

    Args:
        flow_config: Chatbot-specific configuration
        athos_config: Full ATHOS configuration

    Returns:
        Fully initialized chatbot flow
    """
    # Get model config
    if flow_config.model not in athos_config.models:
        raise ValueError(
            f"Model '{flow_config.model}' not found in configuration"
        )
    model_cfg = athos_config.models[flow_config.model]

    # Build model
    model = build_model(model_cfg)

    # Build initial history
    initial_history = cls._build_initial_history(flow_config.initial_history)

    # Construct flow with all dependencies
    return cls(
        model=model,
        system_prompt=flow_config.system_prompt,
        initial_history=initial_history,
        full_config=athos_config
    )
```

**Step 4: Remove initialize() method**
```python
# ❌ DELETE THIS METHOD:
# async def initialize(self, config: BaseFlowConfig) -> None:
#     ...
```

**Step 5: Remove Optional[] from model type**
```python
# In execute() and stream():
# OLD:
if self.model is None:
    raise RuntimeError("Flow not initialized")

# NEW: No check needed, self.model is always available
messages = self._build_messages(input)
response = await self.model.ainvoke(messages)
```

**Step 6: Update registration**
```python
# OLD (at bottom of file):
# def create_langgraph_chatbot_flow(cfg, full_cfg):
#     return LangGraphChatbotFlow(full_config=full_cfg)
#
# register_flow(
#     "langgraph_chatbot",
#     LangGraphChatbotFlowConfig,
#     create_langgraph_chatbot_flow,
#     framework=ToolFramework.LANGGRAPH,
# )

# NEW:
register_flow(LangGraphChatbotFlow)

# Or with decorator:
# @register_flow_type  (add at class definition)
# class LangGraphChatbotFlow(BaseLangGraphFlow):
#     ...
```

**Step 7: Update exports**
```python
__all__ = [
    "LangGraphChatbotFlow",
    "LangGraphChatbotFlowConfig",
    # "create_langgraph_chatbot_flow",  # ❌ Remove if using new pattern only
]
```

### 2.2 Migrate LangGraph React Agent

**File:** `src/athos/frameworks/langgraph/flows/react_agent.py`

**Apply same transformation as chatbot:**
1. Add class metadata
2. Update constructor to take dependencies (model, tools, mcp_clients)
3. Implement create() classmethod that builds all dependencies
4. Remove initialize() method
5. Remove Optional[] types and defensive checks
6. Update registration to use new pattern
7. Ensure cleanup() still closes MCP connections properly

**Key consideration for react_agent:**
```python
async def cleanup(self) -> None:
    """Close MCP client connections."""
    # ✅ Keep this method - it manages real resources
    if self.mcp_clients:
        for client in self.mcp_clients.values():
            await client.close()
```

### 2.3 Testing Requirements

**Test Files:**
- `tests/frameworks/langgraph/test_chatbot.py`
- `tests/frameworks/langgraph/test_react_agent.py`

**Test Cases:**
1. ✅ Flow builds via create() without errors
2. ✅ Flow has no Optional[] types (check isinstance)
3. ✅ execute() works without initialize() call
4. ✅ stream() works without initialize() call
5. ✅ Constructor can be called directly with mocks (for testing)
6. ✅ cleanup() properly releases resources
7. ✅ Integration test through FlowRunner
8. ✅ Config validation catches missing model

**Example Test:**
```python
@pytest.mark.asyncio
async def test_chatbot_create_without_initialize():
    """Test that chatbot works immediately after create()."""
    config = AthosConfig(
        models={"gpt-4": ModelConfig(...)},
        flows={"chatbot": LangGraphChatbotFlowConfig(model="gpt-4")},
        ...
    )

    # Create flow
    flow_config = config.flows["chatbot"]
    flow = await LangGraphChatbotFlow.create(flow_config, config)

    # Should work immediately without initialize()
    input = FlowInput(
        message="Hello",
        session=FlowSession(...),
        mode=ExecutionMode.SYNC,
    )

    output = await flow.execute(input)
    assert output.content  # Should have response
```

### 2.4 Success Criteria

- [ ] Both LangGraph flows use create() pattern
- [ ] No initialize() methods in migrated flows
- [ ] No Optional[] types for dependencies
- [ ] All existing tests pass with minimal changes
- [ ] New tests verify create() pattern works
- [ ] Documentation updated with migration examples

---

## Phase 3: Migrate SmolAgents Flows

**Goal:** Migrate SmolAgents chatbot and agent flows to new interface AND new pattern

**Status:** Not Started
**Estimated Effort:** 2-3 days
**Risk:** 🟡 Medium - larger refactor (interface + pattern)

**Dependencies:** Phase 2 complete

### 3.1 Migrate SmolAgents Chatbot

**File:** `src/athos/frameworks/smolagents/flows/chatbot.py`

**Changes:**

**Step 1: Update to new interface (FlowInput/FlowOutput)**
```python
# OLD:
async def execute(self, input_data: str) -> str:
    return await self.process_message(input_data)

# NEW:
async def execute(self, input: FlowInput) -> FlowOutput:
    # Access message from input
    message = input.message

    # Access history from session (not instance variable!)
    history = input.session.get_history()

    # Process
    response = await self._process_message(message, history)

    # Return structured output
    return FlowOutput(content=response)
```

**Step 2: Remove instance state (conversation_history)**
```python
# OLD:
def __init__(self, model, system_prompt):
    self.model = model
    self.system_prompt = system_prompt
    self.conversation_history = []  # ❌ Instance state

# NEW:
def __init__(self, model, system_prompt, full_config):
    self.model = model
    self.system_prompt = system_prompt
    self._full_config = full_config
    # ❌ No conversation_history - comes from input.session
```

**Step 3: Add class metadata**
```python
class ChatbotFlow(BaseFlow):
    """Simple chatbot flow using SmolAgents."""

    name = "chatbot"
    description = "SmolAgents conversational chatbot"
    config_class = ChatbotFlowConfig
    framework = ToolFramework.SMOLAGENTS
    supported_modes = [ExecutionMode.SYNC]
```

**Step 4: Implement create() classmethod**
```python
@classmethod
async def create(
    cls,
    flow_config: ChatbotFlowConfig,
    athos_config: AthosConfig
) -> ChatbotFlow:
    """Create and initialize SmolAgents chatbot."""
    model_cfg = athos_config.models[flow_config.model]
    model = build_model(model_cfg)

    return cls(
        model=model,
        system_prompt=flow_config.system_prompt,
        full_config=athos_config
    )
```

**Step 5: Update process logic to use session**
```python
async def _process_message(self, message: str, history: List[dict]) -> str:
    """Process a message using session history instead of instance state."""

    # Convert ATHOS history format to SmolAgents format
    smolagents_messages = []
    if self.system_prompt:
        smolagents_messages.append(
            ChatMessage(role="system", content=self.system_prompt)
        )

    # Add history from session
    for msg in history:
        smolagents_messages.append(
            ChatMessage(role=msg["role"], content=msg["content"])
        )

    # Add current message
    smolagents_messages.append(ChatMessage(role="user", content=message))

    # Get response
    try:
        response = self.model(smolagents_messages, stop_sequences=["END"])
        return response.content
    except Exception as e:
        logger.error("Chatbot execution failed: %s", e)
        return f"Error: {e}"
```

**Step 6: Update registration**
```python
register_flow(ChatbotFlow)
```

### 3.2 Migrate SmolAgents Agent

**File:** `src/athos/frameworks/smolagents/flows/agent.py`

**Similar transformation:**
1. Update execute() to FlowInput → FlowOutput
2. Add class metadata
3. Implement create() that builds model, tools, MCP clients
4. Constructor takes all dependencies
5. Update registration

**Key consideration:**
```python
@classmethod
async def create(cls, flow_config: AgentFlowConfig, athos_config: AthosConfig):
    """Build agent with tools and MCP clients."""
    # Build model
    model = build_model(athos_config.models[flow_config.model])

    # Build tools
    tools = []
    for tool_name in flow_config.tools:
        tool = build_tool(tool_name, athos_config)
        tools.append(tool)

    # Build MCP clients
    mcp_clients = {}
    for mcp_name in flow_config.mcp_servers:
        client = await build_mcp_client(mcp_name, athos_config)
        mcp_clients[mcp_name] = client

    return cls(
        model=model,
        tools=tools,
        mcp_clients=mcp_clients,
        agent_type=flow_config.agent_type,
        full_config=athos_config
    )
```

### 3.3 Testing Requirements

**Test both interface change AND pattern change:**
1. ✅ FlowInput → FlowOutput (new interface)
2. ✅ Session history used instead of instance state
3. ✅ create() builds fully-functional flow
4. ✅ No initialize() needed
5. ✅ Works through FlowRunner
6. ✅ LegacyFlowAdapter no longer needed

### 3.4 Success Criteria

- [ ] SmolAgents flows use FlowInput/FlowOutput
- [ ] SmolAgents flows use create() pattern
- [ ] No instance-based conversation state
- [ ] All SmolAgents tests pass
- [ ] LegacyFlowAdapter no longer used for these flows

---

## Phase 4: Cleanup & Finalization

**Goal:** Remove deprecated patterns and simplify codebase

**Status:** Not Started
**Estimated Effort:** 1 day
**Risk:** 🟢 Low - everything already migrated

**Dependencies:** Phases 1-3 complete

### 4.1 Remove Deprecated Code

**Files to update:**

1. **BaseFlow interface** (`src/athos/interfaces/base_flow.py`)
   - Remove `initialize()` method entirely
   - Or mark `@deprecated` if keeping for user extensions

2. **Registry** (`src/athos/registry/flow_registry.py`)
   - Remove legacy overload of `register_flow()`
   - Only keep single-argument version

3. **FlowRunner** (`src/athos/runtime/runner.py`)
   - Remove `_created_via_classmethod` flag check
   - Remove `initialize()` call entirely
   - Simplify `_get_flow()`:
   ```python
   async def _get_flow(self, flow_name: str) -> BaseFlow:
       if flow_name in self._flow_cache:
           return self._flow_cache[flow_name]

       # All flows now use create() pattern
       flow = await build_flow(flow_name, self.config)

       if not is_new_interface(flow):
           flow = LegacyFlowAdapter(flow)

       self._flow_cache[flow_name] = flow
       return flow
   ```

4. **Builder** (`src/athos/runtime/builder.py`)
   - Simplify `build_flow()` - remove legacy factory branch
   ```python
   async def build_flow(flow_name: str, config: AthosConfig) -> BaseFlow:
       """Construct a flow using its create() classmethod."""
       if flow_name not in config.flows:
           raise ValueError(f"Unknown flow: {flow_name}")

       flow_cfg = config.flows[flow_name]
       registration = FLOW_REGISTRY.get(flow_cfg.type)
       if not registration:
           raise ValueError(f"Unknown flow type: {flow_cfg.type}")

       # All flows are now classes with create()
       flow_class = registration.creator
       return await flow_class.create(flow_cfg, config)
   ```

### 4.2 Decide on LegacyFlowAdapter

**Options:**
1. **Keep it** - Allows users to create custom flows with old interface
2. **Remove it** - Force all flows to use new interface

**Recommendation:** Remove LegacyFlowAdapter.

### 4.3 Update Documentation

**Files to update:**
1. `CLAUDE.md`
   - Remove references to old pattern
   - Show only new pattern in examples
   - Update "Adding a New Flow Type" section

2. `README.md`
   - Update examples to use create() pattern
   - Update architecture diagrams if any

3. `docs/athos_openwebui_integration_status.md`
   - Mark migration phases complete

4. Create `docs/flow_migration_guide.md`
   - Step-by-step guide for users migrating custom flows
   - Before/after examples
   - Common pitfalls

### 4.4 Update Examples

**Directory:** `examples/`

Update all example scripts to use new pattern:
```python
# OLD:
flow = create_flow(config, flow_config)
await flow.initialize(config)

# NEW:
flow = await FlowClass.create(flow_config, config)
```

### 4.5 Success Criteria

- [ ] No initialize() in BaseFlow
- [ ] No legacy factory pattern support
- [ ] All built-in flows use create() pattern
- [ ] All tests pass
- [ ] All examples updated
- [ ] Documentation reflects new pattern only
- [ ] Migration guide available for users

---

## Rollback Strategy

Each phase has a clear rollback path:

### Phase 1 Rollback
- Revert commits
- No user-facing impact (changes are additive)

### Phase 2 Rollback
- Revert chatbot.py and react_agent.py
- Re-register with old factory functions
- Tests still pass with old pattern

### Phase 3 Rollback
- Revert smolagents flows
- LegacyFlowAdapter continues to work
- Old string interface restored

### Phase 4 Rollback
- Add back deprecated code
- Both patterns work again

---

## Testing Strategy

### Unit Tests
- Each phase has dedicated test file
- Test both patterns during Phases 1-3
- Test only new pattern in Phase 4

### Integration Tests
- CLI execution through FlowRunner
- Gradio interface (if applicable)
- End-to-end flow execution

### Compatibility Tests
- Ensure LegacyFlowAdapter works (Phases 1-3)
- Ensure old configs work (Phases 1-3)
- Ensure new configs work (all phases)

### Performance Tests
- No performance regression
- Startup time similar or better
- Memory usage similar or better

---

## Migration Checklist

### Phase 1: Dual-Interface Foundation
- [ ] Update BaseFlow with create() abstractmethod
- [ ] Add class metadata to BaseFlow (ClassVar annotations)
- [ ] Update registry with overloaded register_flow()
- [ ] Add register_flow_type() decorator
- [ ] Update build_flow() to detect pattern
- [ ] Update FlowRunner._get_flow() to handle both patterns
- [ ] Write dual-interface tests
- [ ] Update documentation
- [ ] All existing tests pass

### Phase 2: Migrate LangGraph Flows
- [ ] Migrate chatbot.py to create() pattern
- [ ] Migrate react_agent.py to create() pattern
- [ ] Remove initialize() from both
- [ ] Update registrations
- [ ] Write migration tests
- [ ] All LangGraph tests pass

### Phase 3: Migrate SmolAgents Flows
- [ ] Update chatbot.py to FlowInput/FlowOutput
- [ ] Update chatbot.py to create() pattern
- [ ] Update agent.py to FlowInput/FlowOutput
- [ ] Update agent.py to create() pattern
- [ ] Remove instance-based state
- [ ] Update registrations
- [ ] Write migration tests
- [ ] All SmolAgents tests pass

### Phase 4: Cleanup
- [ ] Remove/deprecate initialize() from BaseFlow
- [ ] Simplify registry (remove legacy overload)
- [ ] Simplify build_flow()
- [ ] Simplify FlowRunner._get_flow()
- [ ] Update all documentation
- [ ] Update all examples
- [ ] Write migration guide
- [ ] All tests pass with simplified code

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Dual-Interface | 2-3 days | 2-3 days |
| Phase 2: LangGraph | 1-2 days | 3-5 days |
| Phase 3: SmolAgents | 2-3 days | 5-8 days |
| Phase 4: Cleanup | 1 day | 6-9 days |
| **Total** | **6-9 days** | |

*Estimates assume focused work without major blockers*

---

## Success Metrics

- ✅ Zero uninitialized state windows
- ✅ Zero Optional[] types for flow dependencies
- ✅ Zero defensive `if self.model is None` checks
- ✅ All flows registered with single register_flow() call
- ✅ 100% test coverage for new pattern
- ✅ All existing functionality preserved
- ✅ Documentation complete and accurate

---

## References

- [Original discussion on uninitialized state](Context from chat)
- [Option C analysis](Context from chat)
- [Classmethod factory pattern discussion](Context from chat)
- Python ABC documentation: https://docs.python.org/3/library/abc.html
- PEP 589 (TypedDict): https://peps.python.org/pep-0589/
- typing_extensions.Self: https://peps.python.org/pep-0673/

---

## Notes

- This migration prioritizes **type safety** and **developer experience**
- The classmethod factory pattern is **idiomatic Python** (datetime, Path, dict)
- Class metadata makes registration **discoverable** and **self-documenting**
- Each phase maintains **backward compatibility** until Phase 4
- LegacyFlowAdapter remains for **user extensions**
