# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ATHOS (Agentic Toolkit for HPC Operations Support) is a Python framework for building AI agents that assist with High-Performance Computing (HPC) operations. It provides a configuration-driven architecture supporting multiple agent frameworks (currently SmolAgents and LangGraph) with Model Context Protocol (MCP) integration for connecting to external tools and services.

**⚠️ MAJOR ARCHITECTURAL EVOLUTION IN PROGRESS**: ATHOS is undergoing a significant refactoring to support OpenWebUI Pipelines integration. The new architecture introduces structured data models, a centralized FlowRunner, and rich streaming interfaces. See the "Current Architecture Status" section for details on what's been implemented and what's still in progress.

## Development Setup

### Local Development
```bash
pip install -e .[dev]
```

### NERSC Systems
```bash
./scripts/create_env_nersc.sh
ml conda
conda activate athos
```

### Environment Configuration
Copy `.env.template` to `.env` and configure required environment variables:
- `SERVICENOW_INSTANCE_URL`, `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD` for ServiceNow integration
- `NERSC_CLIENT_ID`, `NERSC_PRIVATE_KEY_PATH` for Superfacility API access
- `CBORG_API_KEY`, `CBORG_API_URL` for CBORG model access
- `ATHOS_WORKSPACE` for shared workspace directory (defaults to `${SCRATCH}/athos/workspace` or `/tmp/athos_workspace`)

## Common Commands

### Running the CLI
```bash
# Basic execution
athos --config config/config.yaml --flow hpc_chatbot --input "what is NERSC?"

# With log level override
athos --config config/config.yaml --flow hpc_chatbot --input "your question" --log-level DEBUG

# With configuration overrides
athos --config config/config.yaml --flow hpc_chatbot --input "hi" \
  --set models.gpt_4o.temperature=0.5 --set models.gpt_4o.max_tokens=50

# Launch Gradio interface
athos --config config/config.yaml --flow hpc_chatbot --gradio --port 7860

# Show configuration summary
athos --config config/config.yaml --show-config
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_factories.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=athos
```

### Evaluations
```bash
# Run evaluations on a flow
python evals/run_evaluations.py --config config/config.yaml --flow hpc_chatbot

# With Q&A dataset
python evals/run_evaluations.py --config config/config.yaml --flow hpc_chatbot --qa-file evals/simple_qa.jsonl

# Multiple flows and custom output
python evals/run_evaluations.py --config config/config.yaml \
  --flow hpc_chatbot --flow docs_rag_agent \
  --output results.json
```

### MCP Server Standalone Execution
```bash
# ServiceNow MCP server
servicenow-mcp

# Superfacility API MCP server
nersc-sfapi-mcp

# RAG MCP server
rag-mcp --repo-url https://example.com/repo.git --docs-path /path/to/docs
```

## Current Architecture Status

ATHOS is in the middle of a major architectural transition. The project is implementing the design outlined in `docs/athos_openwebui_integration_plan_v3.0.md`. Current status is tracked in `docs/athos_openwebui_integration_status.md`.

### What's Been Implemented (✅ Completed Milestones 1-2)

The following components are **fully implemented and tested**:

1. **Structured Data Models** (`athos/models/`):
   - `FlowInput`: Rich input containing message, session, execution mode, and metadata
   - `FlowOutput`: Structured output with content, artifacts (images/files/links), and metadata
   - `FlowSession`: External session state with conversation history, workspace, and custom state
   - `FlowRequest/FlowResult`: Internal execution tracking models
   - `ExecutionMode`: Enum defining SYNC, STREAMING, INTERACTIVE modes
   - All models use **Pydantic** for validation and serialization

2. **Enhanced BaseFlow Interface** (`athos/interfaces/base_flow.py`):
   - `execute(FlowInput) -> FlowOutput`: Primary execution method (all flows implement this)
   - `stream(FlowInput) -> AsyncGenerator[FlowOutput]`: Streaming execution with intermediate updates
   - `initialize(config)`: One-time setup for expensive resources
   - `cleanup()`: Resource cleanup
   - `can_stream()`: Capability detection
   - Class-level metadata: `name`, `description`, `supported_modes`

3. **FlowRunner Orchestration** (`athos/runtime/runner.py`):
   - Central orchestrator managing flow lifecycle, sessions, caching
   - `execute()`: Synchronous flow execution with session management
   - `stream()`: Async streaming execution
   - Automatic flow caching and initialization
   - Comprehensive error handling and logging
   - Session management via SessionStore abstraction

4. **SessionStore** (`athos/runtime/session_store.py`):
   - Abstract interface for session persistence
   - `InMemorySessionStore`: Thread-safe in-memory implementation
   - Supports get_or_create, save, delete, list_sessions operations
   - Ready for Redis/SQL backends (not yet implemented)

5. **Compatibility Layer** (`athos/runtime/compat.py`):
   - `LegacyFlowAdapter`: Wraps old-style flows to work with new Runner
   - Auto-detection of legacy vs new interface flows
   - Seamless migration path without breaking existing code

6. **LangGraph Integration Utilities** (`athos/frameworks/langgraph/utils/translation.py`):
   - `to_langgraph_messages()`: Convert ATHOS session messages to LangChain format
   - `from_langgraph_messages()`: Convert LangChain messages back to ATHOS format
   - `build_langgraph_config()`: Build LangGraph config with `thread_id = session_id`
   - Enables LangGraph to use its own checkpointing while syncing with ATHOS sessions

7. **Migrated LangGraph Chatbot** (`athos/frameworks/langgraph/flows/chatbot.py`):
   - Fully refactored to use `FlowInput`/`FlowOutput`
   - Stateless design (reads history from `input.session`)
   - Supports both `execute()` and `stream()` modes
   - Uses translation utilities for message conversion

8. **Updated CLI** (`athos/main.py`):
   - Now routes execution through `FlowRunner`
   - Handles artifacts (images, files, links)
   - Supports both legacy and new-style flows transparently

### What's NOT Yet Implemented (⏳ Upcoming Milestones 3-6)

The following are **planned but not yet coded**:

- **OpenWebUI Pipeline Integration** (`athos/integrations/openwebui/`): Not created yet
- **Hook System** (`athos/runtime/hooks.py`): Planned for observability/monitoring
- **Event Formatters** for OpenWebUI: Not yet implemented
- **Enhanced LangGraph Streaming**: Basic streaming works, but rich events (thinking blocks, tool status) not yet implemented
- **Production Features**: Timeouts, metrics, health checks not yet added
- **Redis/SQL SessionStore**: Only in-memory implementation exists

### Core Architecture Principles

**Configuration-Driven Design**: All agents, models, tools, and MCP servers are defined in YAML configuration files (`config/config.yaml`). The runtime loads and instantiates components based on these configurations.

**Registry Pattern**: Flows register themselves using `register_flow()` from `athos.registry.flow_registry`. When framework modules are imported, they automatically register their flow types, making them available to the runtime without hardcoded dependencies.

**Flow Abstraction**: All concrete flows implement the `BaseFlow` protocol from `athos.interfaces.base_flow`. The new interface uses `FlowInput` and returns `FlowOutput` (legacy flows returning `str` are automatically adapted).

**MCP Integration**: Tools and services are exposed via Model Context Protocol servers. The framework supports stdio-based MCP servers configured with command, args, and environment variables. MCP clients are instantiated by framework-specific factories.

**Stateless Flows**: Flows are now pure functions over `(input, session) -> output`. State lives in `FlowSession` (managed by `FlowRunner`), not in flow instances. This enables:
- Sharing flow instances across multiple sessions
- Better testability
- Easier horizontal scaling

**Runner-Managed Lifecycle**: `FlowRunner` handles orchestration, session management, caching, error handling. Flows focus purely on business logic.

### Package Structure

The architecture follows a **layered design** with clear separation of concerns:

```
athos/
├── models/                        # 📦 NEW: Pydantic data models (no dependencies)
│   ├── flow.py                   # FlowInput, FlowOutput, Artifact
│   ├── session.py                # FlowSession
│   ├── execution.py              # FlowRequest, FlowResult (internal)
│   └── enums.py                  # ExecutionMode
│
├── interfaces/                    # Contract definitions
│   └── base_flow.py              # BaseFlow protocol (imports from models)
│
├── runtime/                       # 🔄 ENHANCED: Orchestration layer
│   ├── builder.py                # Existing: builds flows from config
│   ├── runner.py                 # NEW: FlowRunner orchestration
│   ├── session_store.py          # NEW: Session persistence abstraction
│   └── compat.py                 # NEW: Legacy flow adapter
│
├── frameworks/                    # Framework implementations
│   ├── langgraph/
│   │   ├── flows/
│   │   │   ├── chatbot.py       # ✅ MIGRATED to new interface
│   │   │   └── react_agent.py   # ⏳ TODO: Migrate to new interface
│   │   ├── utils/
│   │   │   ├── messages.py
│   │   │   └── translation.py   # NEW: LangGraph ↔ ATHOS translation
│   │   └── factories.py
│   └── smolagents/
│       └── flows/                # ⏳ TODO: Migrate to new interface
│
├── integrations/                  # External system integrations
│   ├── servicenow/               # ServiceNow ticket integration
│   ├── slackbot/                 # Slack bot integration
│   └── openwebui/                # ⏳ TODO: OpenWebUI Pipelines (Milestone 3)
│
├── tools/                         # HPC-specific tools and MCP servers
│   ├── slurm_mcp/                # SLURM job management
│   ├── servicenow_mcp/           # ServiceNow MCP server
│   ├── sfapi_mcp/                # NERSC Superfacility API
│   └── rag_mcp/                  # RAG with BM25 search
│
├── config/                        # Configuration models
│   └── models.py                 # Pydantic configs for YAML parsing
│
├── registry/                      # Flow registry
│   └── flow_registry.py          # Dynamic flow registration
│
├── utils/                         # Shared utilities
│   ├── workspace.py              # Workspace management
│   ├── logging.py                # Logging configuration
│   └── config_parser.py          # Config parsing utilities
│
├── examples/                      # ⚠️ TODO: Update for new runtime
│   └── *.py                      # Standalone example scripts
│
└── main.py                        # ✅ UPDATED: CLI using FlowRunner
```

**Key Benefits of New Structure**:
- ✅ **No circular dependencies**: `models/` has no imports from other ATHOS packages
- ✅ **Clear layering**: Models → Interfaces → Runtime → Integrations
- ✅ **Easy imports**: `from athos.models.flow import FlowInput, FlowOutput`
- ✅ **Backward compatible**: Legacy flows work via `LegacyFlowAdapter`

### Configuration Structure

The YAML configuration has four main sections:

1. **`models`**: LLM instances with `model_id`, `api_key`, `api_base`, and generation parameters
2. **`mcp_servers`**: MCP server definitions with `mcp_type`, `command`, `args`, and optional `env` and `instructions`
3. **`tools`**: Non-MCP tools with `callable_name`, `module_path`, `parameters`, and a `framework` indicating the runtime (e.g., `smolagents`, `langgraph`)
4. **`flows`**: Agent flow definitions with `type`, `model`, and framework-specific parameters (e.g., `agent_type`, `mcp_servers`, `tools`, `system_prompt`)

### Flow Types and Frameworks

**SmolAgents Flows** (registered in `src/athos/frameworks/smolagents/flows/`):
- `chatbot`: Simple conversational flow with no tools (⏳ **TODO**: Migrate to new interface)
- `agent`: Tool-calling or code-executing agent (⏳ **TODO**: Migrate to new interface)
  - `agent_type: "tool_calling"`: Uses structured tool calls
  - `agent_type: "code"`: Generates and executes Python code with MCP tools

**LangGraph Flows** (registered in `src/athos/frameworks/langgraph/flows/`):
- `langgraph_chatbot`: ✅ **MIGRATED** - Now uses `FlowInput`/`FlowOutput`, supports streaming
- `langgraph_react_agent`: ✅ **MIGRATED** - Full streaming with tool call events, uses new interface

### New vs Legacy Flow Interface

**New Interface** (all new flows should use this):
```python
from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.enums import ExecutionMode

class MyNewFlow(BaseFlow):
    name = "my_flow"
    description = "Description"
    supported_modes = [ExecutionMode.SYNC, ExecutionMode.STREAMING]

    async def execute(self, input: FlowInput) -> FlowOutput:
        # Access user message
        message = input.message

        # Access session history
        history = input.session.get_history()

        # Do work...
        result = await self.process(message, history)

        # Return structured output
        return FlowOutput(
            content=result,
            artifacts=[],  # Optional: images, files, links
            metadata={"tokens": 100}  # Optional: execution metadata
        )

    async def stream(self, input: FlowInput) -> AsyncGenerator[FlowOutput, None]:
        """Optional: implement for true streaming"""
        # Yield intermediate updates
        yield FlowOutput(content="Thinking...", metadata={"chunk": True})

        # Yield final result
        result = await self.execute(input)
        yield result
```

**Legacy Interface** (automatically adapted):
```python
class MyLegacyFlow:
    async def execute(self, input_data: str) -> str:
        return f"Response to: {input_data}"
```

The `LegacyFlowAdapter` in `athos/runtime/compat.py` automatically wraps legacy flows, so they continue to work with `FlowRunner`. However, **all new flows should use the new interface** for access to:
- Session history and state
- Artifact support (images, files)
- Rich metadata
- True streaming capabilities

### Extending the Framework

**Adding a New Flow Type** (using new interface):
1. Create a class implementing `BaseFlow` from `athos.interfaces.base_flow`
2. Implement `execute(FlowInput) -> FlowOutput` (required)
3. Optionally implement `stream(FlowInput) -> AsyncGenerator[FlowOutput]` for streaming
4. Optionally implement `initialize(config)` for expensive setup
5. Set class-level metadata: `name`, `description`, `supported_modes`
6. Create a factory function: `(config: ConfigModel, flow_config: FlowConfig) -> BaseFlow`
7. Call `register_flow("your_flow_type", factory_function)` at module import
8. Add your flow to a config.yaml `flows:` section

**Example**:
```python
# src/athos/frameworks/myframework/flows/my_flow.py
from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.enums import ExecutionMode
from athos.registry.flow_registry import register_flow

class MyCustomFlow(BaseFlow):
    name = "my_custom"
    description = "Custom flow example"
    supported_modes = [ExecutionMode.SYNC]

    async def initialize(self, config):
        self.model = load_model(config.model)

    async def execute(self, input: FlowInput) -> FlowOutput:
        response = await self.model.generate(input.message)
        return FlowOutput(content=response)

# Factory function
def create_my_custom_flow(config, flow_config):
    return MyCustomFlow()

# Register at module load
register_flow("my_custom", create_my_custom_flow)
```

**Adding a New Tool**:
- For MCP tools: Define an MCP server in the `mcp_servers` section of config.yaml with command, args, and environment variables
- For regular tools: Add to the `tools` section with `callable_name`, `module_path`, and an explicit `framework` matching the target flow runtime

**Working with LangGraph Flows**:
LangGraph flows have special integration considerations:
- Use `athos.frameworks.langgraph.utils.translation` utilities to convert messages
- LangGraph manages its own checkpointing using `thread_id = session_id`
- Sync conversation history back to `FlowSession.messages` for consistency
- See `athos/frameworks/langgraph/flows/chatbot.py` for reference implementation

### Session and Workspace Management

**Session Management** (new in refactoring):
- Sessions are managed by `FlowRunner` via the `SessionStore` abstraction
- Each session has a unique `session_id` and contains:
  - Conversation history (`messages`: list of `{"role": "user/assistant", "content": "..."}`)
  - Workspace directory for file storage
  - Custom state dictionary for flow-specific data
  - Metadata (created_at, updated_at, interface)
- Current implementation: `InMemorySessionStore` (loses state on restart)
- Future: Redis or SQL-backed stores for persistence across restarts

**Workspace Directories**:
- Each session gets its own workspace: `<base>/<user_id>/<session_id>/`
- Base path configured via `ATHOS_WORKSPACE` env var or `workspace_path` in config
- Defaults to `${SCRATCH}/athos/workspace` on NERSC or `/tmp/athos_workspace` elsewhere
- Flows can read/write files to `input.session.workspace` path
- Use `athos.utils.workspace` helpers to manage workspace contents

## Testing Strategy

- **Unit tests**: Test individual components in isolation using mocks
  - ✅ Models: Serialization, validation, state management (`tests/models/`)
  - ✅ SessionStore: Concurrent access, session isolation (`tests/runtime/test_session_store.py`)
  - ✅ FlowRunner: Execution, caching, error handling (`tests/runtime/test_runner.py`)
  - ✅ Compatibility: Legacy flow adaptation (`tests/runtime/test_compat.py`)
  - ✅ LangGraph translation: Message conversion, config building (`tests/frameworks/langgraph/test_translation.py`)
- **Integration tests**: Test CLI execution and flow creation from configuration
  - ✅ CLI using FlowRunner (`tests/test_cli_integration.py`)
  - ⏳ TODO: OpenWebUI Pipeline integration tests (Milestone 3)
- **Evaluation pipeline**: ⚠️ **TODO**: Update for new runtime
  - End-to-end tests using synthetic HPC scenarios in `evals/` directory
  - Q&A datasets and structured test cases
  - Currently uses legacy interface; needs updating for `FlowRunner`
- **Framework-specific tests**:
  - ✅ LangGraph: State management, checkpointing, message translation
  - ServiceNow MCP: Authentication, incident operations, read-only mode

## Configuration Overrides

Use `--set` with dot notation to override config values at runtime:
```bash
--set models.gpt_4o.temperature=0.5
--set flows.hpc_chatbot.system_prompt="Custom prompt"
```

Values are parsed as YAML, so wrap strings in quotes. Nested dictionary keys are separated by dots.

## Logging

Logging is configured via the `logging_config` section in YAML:
- Simple format: `level` and `format` keys passed to `logging.basicConfig`
- Handler-based: Specify `handlers` array with `type: console` or `type: file`
- Full dictConfig: Include `version` key for complete `logging.config.dictConfig` specification

Log levels: DEBUG, INFO, WARNING, ERROR. Use `--log-level` CLI flag to override for a single run.

## Important Implementation Notes

### General
- **Async execution**: All flow `execute()` methods are async; use `asyncio.run()` or `await` appropriately
- **Environment variable expansion**: Config values support `${VAR_NAME}` and `${VAR_NAME:-default}` syntax
- **MCP server lifecycle**: MCP clients manage server processes; ensure proper cleanup to avoid orphaned processes
- **Tool instructions**: Use the `instructions` field in MCP server configs to provide agent-specific guidance on tool usage

### New Runtime Architecture
- **FlowRunner manages sessions**: Don't create sessions manually; `FlowRunner.execute()` handles this
- **Flows are stateless**: Never store conversation history in flow instance variables; always use `input.session`
- **Pydantic models everywhere**: Use `.model_dump()` for serialization, not manual `to_dict()` methods
- **Legacy flows work automatically**: `FlowRunner` detects and adapts old-style flows via `LegacyFlowAdapter`
- **Session persistence**: Current `InMemorySessionStore` loses data on restart; production deployments will need Redis/SQL backend

### Framework-Specific
- **SmolAgents code agents**: The `additional_authorized_imports` field controls which Python modules can be imported in generated code (⏳ not yet migrated to new interface)
- **LangGraph checkpointing**:
  - LangGraph manages its own state using `thread_id = session_id`
  - Use `athos.frameworks.langgraph.utils.translation.build_langgraph_config()` to create config
  - Always sync final messages back to `input.session.messages` for consistency
  - For persistent checkpointing, configure a file-based `SqliteSaver` instead of `:memory:`
  - See `chatbot.py` for reference implementation

### Migration Path
- **All new flows**: Use `FlowInput`/`FlowOutput` interface from `athos.models.flow`
- **Existing flows**: Continue to work but won't have access to sessions, artifacts, or streaming
- **Examples and evals**: Need updating to use new `FlowRunner` API
- **Priority for migration**:
  1. ✅ LangGraph chatbot (complete)
  2. ✅ LangGraph ReAct agent (complete)
  3. ⏳ SmolAgents flows
  4. ⏳ Example scripts
  5. ⏳ Evaluation harness

**LangGraph Note**: Both LangGraph flows now inherit from `BaseLangGraphFlow` which provides shared utilities like `_get_model_config()`. When creating new LangGraph flows, extend this base class for consistency.

## Refactoring Roadmap

The OpenWebUI integration plan is documented in detail in `docs/athos_openwebui_integration_plan_v3.0.md`. Current progress is tracked in `docs/athos_openwebui_integration_status.md`.

### Completed Milestones

**Milestone 1: Core Runtime Foundation** ✅
- Pydantic data models package (`athos/models/`)
- SessionStore abstraction with in-memory implementation
- Enhanced BaseFlow interface
- FlowRunner orchestration layer
- Comprehensive tests

**Milestone 2: Runtime Compatibility** ✅
- Legacy flow adapter
- LangGraph translation utilities
- LangGraph chatbot migrated to new interface
- CLI updated to use FlowRunner

### Current Focus

**Milestone 3: OpenWebUI Pipeline Integration** ⏳ (NOT STARTED)

The next major task is creating the OpenWebUI Pipeline adapter:

**What needs to be built**:
1. `athos/integrations/openwebui/pipeline.py`: Pipeline class implementing OpenWebUI protocol
2. `athos/integrations/openwebui/formatters.py`: Event formatting utilities
3. Docker Compose deployment configuration
4. Integration tests with mock OpenWebUI requests

**Key design points**:
- Pipeline is a thin adapter translating OpenWebUI protocol to FlowRunner calls
- Uses Valves (Pydantic BaseModel) for user-configurable settings
- Supports both sync and streaming execution
- Formats FlowOutput artifacts as markdown for display in OpenWebUI
- Emits status events during streaming

**Reference implementations**:
- See `docs/athos_openwebui_integration_plan_v3.0.md` for detailed Pipeline class design
- Look at Alpha Berkeley patterns for valve configuration and streaming

### Upcoming Milestones

**Milestone 4: Hook System** ⏳
- Event hooks for observability (BEFORE_EXECUTE, OUTPUT_CHUNK, AFTER_SUCCESS/ERROR)
- Built-in hooks for logging and metrics
- Integration with FlowRunner

**Milestone 5: Enhanced LangGraph Streaming** ⏳
- Rich streaming events (thinking blocks, tool calls, status updates)
- LangGraph custom events via `get_stream_writer()`
- OpenWebUI event formatter for all event types

**Milestone 6: Production Hardening** ⏳
- Timeouts and cancellation
- Prometheus metrics
- Health check endpoints
- Persistent SessionStore backends (Redis, SQL)

## Guidelines for Coding Agents

### When Working on ATHOS Code

**1. Understand the context**:
- Read `docs/athos_openwebui_integration_status.md` for current status
- Check if component is migrated (✅), in progress (⏳), or not started
- Refer to `docs/athos_openwebui_integration_plan_v3.0.md` for detailed design

**2. Follow the new patterns**:
- **All new flows**: Implement `BaseFlow` with `FlowInput`/`FlowOutput`
- **All data models**: Use Pydantic BaseModel (already done in `athos/models/`)
- **Session access**: Always use `input.session`, never store state in flow instances
- **Artifacts**: Use `FlowOutput.artifacts` for images, files, links
- **Metadata**: Use `FlowOutput.metadata` for execution details (tokens, tools used, etc.)

**3. Maintain backward compatibility**:
- Don't break existing flows during migration
- Use `LegacyFlowAdapter` for old-style flows
- Test both new and legacy flows work with FlowRunner

**4. Testing requirements**:
- Write unit tests for all new components
- Update integration tests when changing interfaces
- Ensure 90%+ coverage for new code
- Test concurrent scenarios for session management

**5. Documentation**:
- Update docstrings with Pydantic model details
- Add examples showing new interface usage
- Document migration steps for similar components
- Keep CLAUDE.md and status docs in sync

### Common Pitfalls to Avoid

❌ **DON'T**:
- Store conversation history in flow instance variables
- Create sessions manually (let FlowRunner do it)
- Use `to_dict()` methods (Pydantic provides `.model_dump()`)
- Assume sessions persist across restarts (current backend is in-memory)
- Break the layering: models should have no dependencies on runtime/flows

✅ **DO**:
- Access history via `input.session.get_history()`
- Return rich `FlowOutput` with artifacts and metadata
- Use async/await for all flow methods
- Handle errors gracefully and return them in `FlowOutput`
- Sync LangGraph state back to `FlowSession.messages` for consistency

### Example: Migrating a Legacy Flow

**Before** (legacy interface):
```python
class MyOldFlow:
    def __init__(self):
        self._history = []  # ❌ State in instance

    async def execute(self, input_data: str) -> str:  # ❌ String I/O
        self._history.append(input_data)
        response = await self.process(input_data)
        self._history.append(response)
        return response
```

**After** (new interface):
```python
from athos.interfaces.base_flow import BaseFlow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.enums import ExecutionMode

class MyNewFlow(BaseFlow):
    name = "my_flow"
    description = "Migrated flow"
    supported_modes = [ExecutionMode.SYNC]

    async def execute(self, input: FlowInput) -> FlowOutput:  # ✅ Structured I/O
        # ✅ Read history from session
        history = input.session.get_history()

        # Do processing
        response = await self.process(input.message, history)

        # ✅ Return structured output
        return FlowOutput(
            content=response,
            metadata={"history_length": len(history)}
        )
```

### Getting Help

- **Design questions**: Refer to `docs/athos_openwebui_integration_plan_v3.0.md`
- **Current status**: Check `docs/athos_openwebui_integration_status.md`
- **Reference implementations**:
  - New interface: `athos/frameworks/langgraph/flows/chatbot.py`
  - LangGraph integration: `athos/frameworks/langgraph/utils/translation.py`
  - FlowRunner usage: `athos/main.py` (CLI)
- **Data models**: All Pydantic models in `athos/models/`
