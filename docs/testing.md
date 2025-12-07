# Testing Guide

## Directory layout
- `tests/unit/`: fast, isolated tests that mock external systems. Mirrors `src/athos/...` with subfolders like `config`, `registry`, `runtime`, `frameworks/<name>`, `tools/<name>`.
- `tests/integration/`: cross-component and IO-oriented cases, including flow/CLI evaluations and external tool integrations. Subfolders: `flows/<framework>`, `tools/<name>`, `openwebui/`, etc.

## Markers
- `unit`: applied automatically to everything under `tests/unit/`.
- `integration`: applied automatically to everything under `tests/integration/`.
- `slow`: opt-in for particularly long-running cases.

Markers are registered in `pyproject.toml` and enforced via `tests/unit/conftest.py` and `tests/integration/conftest.py`.

## Common commands
- Run all unit tests: `pytest tests/unit` or `pytest -m unit`
- Run integration tests: `pytest tests/integration` or `pytest -m integration`
- Exclude slow tests: `pytest -m 'unit and not slow'`
- Focus on a slice: e.g., `pytest tests/unit/frameworks/langgraph -q`

## Fixture scoping
- Unit tests get the autouse `isolate_flow_registry` fixture from `tests/unit/conftest.py` so flow registry state is reset between cases.
- Integration tests intentionally avoid that fixture to allow realistic registry wiring.
