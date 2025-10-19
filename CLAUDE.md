# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ATHOS (Agentic Toolkit for HPC Operations Support) is a Python framework for building AI agents that assist with High-Performance Computing (HPC) operations. It provides a configuration-driven architecture supporting multiple agent frameworks (currently SmolAgents and LangGraph) with Model Context Protocol (MCP) integration for connecting to external tools and services.

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

## Architecture

### Core Components

**Configuration-Driven Design**: All agents, models, tools, and MCP servers are defined in YAML configuration files (`config/config.yaml`). The runtime loads and instantiates components based on these configurations.

**Registry Pattern**: Flows register themselves using `register_flow()` from `athos.registry.flow_registry`. When framework modules are imported, they automatically register their flow types, making them available to the runtime without hardcoded dependencies.

**Flow Abstraction**: All concrete flows implement the `BaseFlow` protocol from `athos.interfaces.base_flow`, which requires an `async def execute(input_data: str) -> Any` method. This enables framework-agnostic execution.

**MCP Integration**: Tools and services are exposed via Model Context Protocol servers. The framework supports stdio-based MCP servers configured with command, args, and environment variables. MCP clients are instantiated by framework-specific factories.

### Package Structure

- **`src/athos/interfaces/`**: Shared `BaseFlow` protocol that all flow implementations must satisfy
- **`src/athos/registry/`**: Flow registry (`FLOW_REGISTRY`) and `register_flow()` helper for dynamic flow registration
- **`src/athos/runtime/`**: `build_config()`, `build_flow()`, and `create_flows()` functions that construct flows from YAML configuration
- **`src/athos/config/`**: Pydantic models for configuration validation (`models.py`)
- **`src/athos/frameworks/smolagents/`**: SmolAgents implementation with `factories.py` for building models/tools/MCP clients and `flows/` containing agent and chatbot flows
- **`src/athos/frameworks/langgraph/`**: LangGraph implementation with similar structure to smolagents
- **`src/athos/tools/`**: HPC-specific tools and MCP servers:
  - `slurm_query.py`: SLURM job query utility
  - `slurm_mcp/`: MCP server for SLURM commands
  - `servicenow_mcp/`: ServiceNow integration MCP server
  - `sfapi_mcp/`: NERSC Superfacility API MCP server
  - `rag_mcp/`: Retrieval-augmented generation MCP server with BM25 search
- **`src/athos/examples/`**: Standalone example scripts demonstrating agent usage
- **`src/athos/utils/`**: Shared utilities including workspace management, logging, and configuration parsing
- **`src/athos/main.py`**: CLI entry point (`cli()` function)

### Configuration Structure

The YAML configuration has four main sections:

1. **`models`**: LLM instances with `model_id`, `api_key`, `api_base`, and generation parameters
2. **`mcp_servers`**: MCP server definitions with `mcp_type`, `command`, `args`, and optional `env` and `instructions`
3. **`tools`**: Non-MCP tools with `callable_name`, `module_path`, and `parameters`
4. **`flows`**: Agent flow definitions with `type`, `model`, and framework-specific parameters (e.g., `agent_type`, `mcp_servers`, `tools`, `system_prompt`)

### Flow Types and Frameworks

**SmolAgents Flows** (registered in `src/athos/frameworks/smolagents/flows/`):
- `chatbot`: Simple conversational flow with no tools
- `agent`: Tool-calling or code-executing agent
  - `agent_type: "tool_calling"`: Uses structured tool calls
  - `agent_type: "code"`: Generates and executes Python code with MCP tools

**LangGraph Flows** (registered in `src/athos/frameworks/langgraph/flows/`):
- `langgraph_chatbot`: Simple stateful chatbot
- `langgraph_react_agent`: ReAct-style agent with tool calling

### Extending the Framework

**Adding a New Flow Type**:
1. Create a class implementing `BaseFlow` with `async def execute(input_data: str) -> Any`
2. Create a factory function matching the `FlowFactory` signature: `(config: ConfigModel, flow_config: FlowConfig) -> BaseFlow`
3. Call `register_flow("your_flow_type", factory_function)` when your module is imported
4. Import your module from the main package or ensure it's loaded during runtime

**Adding a New Tool**:
- For MCP tools: Define an MCP server in the `mcp_servers` section of config.yaml with command, args, and environment variables
- For regular tools: Add to the `tools` section with `callable_name` and `module_path` pointing to the tool class

### Workspace Management

The shared workspace (`ATHOS_WORKSPACE` env var or `workspace_dir` in config) allows files generated by one component (e.g., downloaded attachments) to be accessed by others. The filesystem MCP server is granted write access to this directory. Use helpers from `athos.utils.workspace` to inspect or clear workspace contents.

## Testing Strategy

- **Unit tests**: Test individual components (factories, registry, utilities) in isolation using mocks
- **Integration tests**: Test CLI execution and flow creation from configuration
- **Evaluation pipeline**: End-to-end tests using synthetic HPC scenarios in `evals/` directory with Q&A datasets and structured test cases
- LangGraph tests verify state management and checkpointing behavior
- ServiceNow MCP tests validate authentication, incident operations, and read-only mode

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

- **Async execution**: All flow `execute()` methods are async; use `asyncio.run()` or `await` appropriately
- **Environment variable expansion**: Config values support `${VAR_NAME}` and `${VAR_NAME:-default}` syntax
- **MCP server lifecycle**: MCP clients manage server processes; ensure proper cleanup to avoid orphaned processes
- **SmolAgents code agents**: The `additional_authorized_imports` field controls which Python modules can be imported in generated code
- **LangGraph state management**: LangGraph flows use checkpointing for conversation history; state is persisted in memory by default
- **Tool instructions**: Use the `instructions` field in MCP server configs to provide agent-specific guidance on tool usage
