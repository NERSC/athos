# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Overview

ATHOS (Agentic Toolkit for HPC Operations Support) is a Python framework for building AI agents for HPC operations workflows.

Current architecture is **FlowRunner-first**:
- Flows implement `BaseFlow` and use async `create()` + `execute()` methods.
- Execution uses structured models (`FlowInput`, `FlowOutput`, `FlowSession`, `FlowResult`).
- Session lifecycle is orchestrated by `FlowRunner`.
- OpenWebUI manifold integration is implemented and available in `integrations/openwebui/`.

Treat migration-era notes as historical unless reflected in current code.

## Development Setup

Local:
```bash
pip install -e .[dev]
```

NERSC:
```bash
./scripts/create_env_nersc.sh
ml conda
conda activate athos
```

Environment:
```bash
cp .env.template .env
```
Then set credentials/secrets as needed (ServiceNow, SFAPI, CBORG, etc.).

## Common Commands

CLI:
```bash
athos --config config/config.yaml --flow lang_chat --input "what is NERSC?"
athos --config config/config.yaml --flow lang_chat --input "hi" --set models.gpt_4o.temperature=0.5
athos --config config/config.yaml --show-config
athos --config config/config.yaml --flow smol_basic_agent --gradio --port 7860
```

Tests:
```bash
pytest
pytest tests/unit
pytest tests/integration
pytest -m 'unit and not slow'
```

Evaluations:
```bash
python evals/run_evaluations.py --config config/config.yaml --flow lang_chat
```

OpenWebUI demo stack:
```bash
docker compose -f integrations/openwebui/docker-compose.yml up --build
```

## Current Architecture (Source of Truth)

Primary runtime/data components:
- `src/athos/interfaces/base_flow.py`
- `src/athos/runtime/runner.py`
- `src/athos/runtime/builder.py`
- `src/athos/runtime/session_store.py`
- `src/athos/models/flow.py`
- `src/athos/models/session.py`
- `src/athos/models/execution.py`

Flow implementations:
- `src/athos/frameworks/smolagents/flows/agent.py` (`smol_agent`)
- `src/athos/frameworks/langgraph/flows/chatbot.py` (`langgraph_chatbot`)
- `src/athos/frameworks/langgraph/flows/agent.py` (`langchain_agent`)

Configuration and flow registration:
- `config/config.yaml`
- `src/athos/config/models.py`
- `src/athos/registry/flow_registry.py`

OpenWebUI integration:
- `integrations/openwebui/pipelines/athos_flowrunner_manifold_pipeline.py`
- `integrations/openwebui/docker-compose.yml`
- `docs/openwebui_pipelines_quickstart.md`

## Flow Contract Requirements

All flows should follow `BaseFlow`:
1. Define class metadata (`name`, `description`, `config_class`, `framework`, `supported_modes`).
2. Implement `@classmethod async create(flow_config, athos_config)`.
3. Implement `async execute(input: FlowInput) -> FlowOutput`.
4. Implement `stream()` when true streaming is supported.
5. Keep flow instances stateless with respect to conversation history.

Session/history rules:
- Access history via `input.session`.
- Do not maintain per-conversation state in flow instance fields.
- Let `FlowRunner` manage session persistence.

## OpenWebUI Status

OpenWebUI integration is implemented (not an in-progress migration):
- FlowRunner-backed manifold pipeline is available and tested.
- Streaming SSE output and final-chunk metadata handling are covered by integration tests under `tests/integration/openwebui/`.
- A hello-world manifold pipeline remains as a lightweight reference/template.

Remaining enhancements (if needed) are incremental hardening features, not foundational migration work.

## Testing Guidance

Use `docs/testing.md` conventions:
- Unit tests in `tests/unit/`.
- Integration tests in `tests/integration/`.
- Markers: `unit`, `integration`, `slow`.

When changing runtime, flow, or pipeline behavior:
- Add/adjust unit tests near the modified package.
- Add integration coverage for cross-component behavior (especially streaming/session behavior).

## Coding Guidelines

- Keep changes configuration-driven and registry-compatible.
- Prefer typed, Pydantic-backed models over ad hoc dict payloads.
- Preserve async execution semantics; avoid blocking I/O on hot paths.
- For structured outputs, use `FlowOutput.content`, `FlowOutput.artifacts`, and `FlowOutput.metadata` consistently.
- Keep docs aligned with shipped behavior (avoid roadmap text that contradicts code reality).

## Useful Entry Points

- CLI: `src/athos/main.py`
- Runtime orchestration: `src/athos/runtime/runner.py`
- Example scripts: `src/athos/examples/`
- MCP tools: `src/athos/tools/`
- Testing guide: `docs/testing.md`

## Notes for Future Edits

If you update architecture or workflows, update these together:
- `AGENTS.md`
- `README.md` (user-facing behavior)
- Relevant docs under `docs/`
- Tests that encode the expected behavior

## CUG Paper Context

There is an active CUG paper workstream with versioned planning and experiment drafts:
- `docs/cug_paper/PLAN.md` is the main coordination document (scope, milestones, and near-term execution checklist).
- `docs/cug_paper/EXPERIMENTS_V0.md` tracks the v0 experiment axes and selected experiment set.

Current focus is on M1 baseline execution using the upgraded eval pipeline, dataset curation (Q&A + single-turn ticket scenarios), and retrieval experiments that include historical ServiceNow ticket corpus ingestion.
