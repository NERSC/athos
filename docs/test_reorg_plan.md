# Test Suite Reorganization Plan

Goal: make the test layout consistent, discoverable, and fast to target (unit vs integration). This plan is meant for another contributor to execute.

## 1) Introduce a clear directory schema
- Create `tests/unit/` to mirror `src/athos/...` and hold fast, isolated tests.
  - Move package-aligned files into subfolders: `tests/unit/config`, `tests/unit/registry`, `tests/unit/utils`, `tests/unit/tools/<tool_name>`, etc.
  - Keep existing aligned folders (`tests/models`, `tests/runtime`, `tests/interfaces`, `tests/frameworks/langgraph`) but relocate them under `tests/unit/` while preserving their internal structure.
- Create `tests/integration/` for cross-component/IO/CLI flows.
  - Move `tests/integration/test_agent_checkpoint_integration.py` here (keep name).
  - Move CLI/flow/evaluations and external-system cases (ServiceNow, SF API, OpenWebUI) here.
  - Collapse `tests/integrations/openwebui/...` into `tests/integration/openwebui/...` to remove plural mismatch.
- Create `tests/examples/` (optional) for example notebooks/flows if they are not strictly unit or integration; otherwise place them in unit/integration based on behavior.

## 2) Apply pytest markers for suite selection
- In `pyproject.toml`, add markers: `unit`, `integration`, and optionally `slow` (if any tests are notably long).
- Annotate tests:
  - Unit tests: `@pytest.mark.unit` or set a `pytestmark = pytest.mark.unit` at the module level in each file under `tests/unit/`.
  - Integration tests: `@pytest.mark.integration` in files under `tests/integration/`.
  - Add `@pytest.mark.slow` where appropriate (e.g., network-heavy or large flow runs).
- Optionally add a `tests/conftest.py` hook to warn when both `--unit` and `--integration` are combined, or to default to unit-only when no marker is specified (if desired).

## 3) Scope shared fixtures appropriately
- Move the autouse `isolate_flow_registry` fixture from `tests/conftest.py` into `tests/unit/conftest.py` so it does not affect integration/e2e runs.
- Keep only truly global fixtures in `tests/conftest.py` (e.g., marker registration). Add a `pytest_configure` there to register marker metadata.

## 4) Perform the file moves (no code changes expected)
- Example mapping (adjust as needed):
  - `tests/test_config_models.py` -> `tests/unit/config/test_config_models.py`
  - `tests/test_config_utils.py` -> `tests/unit/config/test_config_utils.py`
  - `tests/test_flow_registry.py` -> `tests/unit/registry/test_flow_registry.py`
  - `tests/test_factories.py`, `tests/test_langgraph_factories.py` -> `tests/unit/frameworks/...` (decide per ownership)
  - `tests/test_logging_utils.py`, `tests/test_notebook_utils.py`, `tests/test_rag_bm25.py` -> `tests/unit/utils/...` (or `tools/` for rag)
  - ServiceNow and SF API files -> `tests/integration/tools/servicenow_mcp/...`, `tests/integration/tools/sfapi_mcp/...`
  - CLI/flow/evaluations (`test_main_cli.py`, `test_run_evaluations.py`, `test_agent_flow_instructions.py`, `test_langchain_agent_flow.py`, `test_langgraph_chatbot_flow.py`, `test_langchain_agent_example.py`) -> `tests/integration/flows/...` (group by framework if helpful).
  - `tests/integrations/openwebui/test_non_streaming_flow_final_chunk.py` -> `tests/integration/openwebui/test_non_streaming_flow_final_chunk.py`
  - Keep `tests/frameworks/langgraph/test_agent_checkpoint.py` as unit unless it requires external services; otherwise move to integration.

## 5) Update import paths and conftest discovery if needed
- Ensure relative imports in tests still resolve; adjust `sys.path` manipulations only if they break after moves (the repo uses src layout, so moving tests should not affect imports).
- Add `tests/unit/conftest.py` if needed for unit-only fixtures (e.g., registry isolation).
- Keep `tests/conftest.py` minimal for shared hooks/markers.

## 6) Documentation and developer ergonomics
- Add README snippet (or `docs/testing.md`) describing:
  - Directory structure and intent.
  - How to run suites: `pytest tests/unit`, `pytest -m integration`, `pytest -m "unit and not slow"`, etc.
  - Marker meanings and expectations (unit = fast/isolated, integration = cross-component/IO, slow = opt-in).

## 7) Clean up caches
- Remove `tests/__pycache__` artifacts and ensure `.gitignore` already covers them (it does). Optional: add a `make clean` target to wipe `__pycache__` and `.pytest_cache`.

## 8) Validation
- Run: `pytest -m unit` (should be fast and isolated).
- Run: `pytest -m integration` (may require env vars for ServiceNow/SF API; document skips/xfails as needed).
- Fix any skipped/broken tests exposed by the move (e.g., missing fixtures).

## 9) Optional refinements
- If integration tests rely on external creds, add `pytest.skip` guards when env vars are missing.
- Consider a `tox`/`nox` or `Makefile` target for `unit`, `integration`, and `all` to standardize CI usage.
