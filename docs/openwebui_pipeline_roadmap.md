# OpenWebUI Pipeline Roadmap (2025 Q2 Refresh)

_Last updated: 2025-06-02_

## Current Snapshot

Athos now exposes flows to OpenWebUI through the `FlowRunner`-backed manifold pipeline (`integrations/openwebui/pipelines/athos_flowrunner_manifold_pipeline.py`). The adapter supports synchronous and streaming execution, translates artifacts into markdown, and respects the shared `FlowOutput` metadata contract (`streaming`, `final`, `status_message`, etc.). Sessions are still persisted in-memory, and there is only rudimentary handling for status text, tool usage, and other non-chat events.

The quickstart in `docs/openwebui_pipelines_quickstart.md` remains accurate for spinning up the current pipeline stack. This roadmap replaces the archived integration status and plan documents and should be treated as the single source of truth for OpenWebUI pipeline work moving forward.

## Milestone Overview

| Milestone | Objective | Themes |
| --- | --- | --- |
| M1. Durable Sessions | Swap in persistent stores and polish session ergonomics. | Redis/Postgres backends, session UX, migration tooling |
| M2. Rich Event Semantics | Extend metadata + streaming surface for reasoning, status, and tool lifecycle events. | Event schema, SSE formatting, formatter utilities |
| M3. Tool Telemetry & Runtime Hooks | Emit detailed tool traces and unify observability hooks. | Tool events, tracing, metrics |
| M4. Reliability & Automation | Establish automated coverage and harden error handling. | Tests, mocks, validation, CI integration |
| M5. Documentation & Adoption | Refresh docs, examples, and migration guidance. | Docs, quickstart updates, rollout plan |

Each milestone below lists concrete tasks with enough context for an engineer or coding agent to execute independently. Tasks are prioritized in execution order unless otherwise noted.

---

## Milestone M1 – Durable Sessions

1. **Implement Redis `SessionStore` backend**  
   - Location: `src/athos/runtime/session_store/` (create subpackage if needed).  
   - Provide async CRUD mirroring the in-memory store; support configurable TTL.  
   - Add valve configuration to the pipeline (`integrations/openwebui/pipelines/...`) to select backend + connection settings.

2. **Add SQL (Postgres) `SessionStore` backend (stretch)**
   - Reuse SQLAlchemy core models if available; otherwise create lightweight table schema.
   - Provides multi-region durability, transactional consistency, and richer querying for audit/reporting use cases.
   - Include migration guidance or simple alembic stub.

3. **Session migration + health checks**
   - Add CLI utilities in `scripts/` to migrate session data between backends, so operators can promote from in-memory/Redis to Postgres without losing history.
   - Document how migrations cover TTL vs. non-expiring records and provide dry-run verification steps.
   - Expose liveness checks in the pipeline (e.g., optional `/healthz` route if the server supports it) to validate connectivity at startup and surface alerts early.

4. **Session UX improvements**  
   - Ensure history replay uses persisted sessions exclusively (audit `FlowRunner`).  
   - Provide valve toggles for auto-reset, TTL, and maximum transcript length; document defaults in quickstart.

**Exit criteria:** Redis backend in production use, automated smoke test covering resume across restarts, updated quickstart instructions.

---

## Milestone M2 – Rich Event Semantics

1. **Define `FlowOutput.metadata.event_type` schema**  
   - Extend models in `src/athos/models/flow.py` with typed enums for events (`chat`, `status`, `reasoning`, `tool_start`, etc.).  
   - Document serialization requirements and ensure backwards compatibility.

2. **Introduce OpenWebUI event formatter module**  
   - Create `integrations/openwebui/formatters/events.py` to map `FlowOutput` + metadata into SSE payloads.  
   - Ensure status/reasoning events emit as SSE `event` types rather than transcript text.

3. **Update pipeline stream handling**  
   - Refactor `pipe()` streaming loop to delegate formatting to the new module.  
   - Guarantee transcript persistence excludes reasoning/status-only events by default.

4. **Backfill flow emitters**  
   - Update representative flows (`src/athos/flows/...` or LangGraph adapters) to populate reasoning/status metadata for known steps.  
   - Provide guidelines for other flow authors via docstring or developer guide snippet.

**Exit criteria:** Pipeline produces distinct SSE events for chat, status, and reasoning content; transcripts remain clean; documentation explains the event taxonomy.

---

## Milestone M3 – Tool Telemetry & Runtime Hooks

1. **Tool lifecycle metadata**  
   - Expand metadata schema with `tool_name`, `call_id`, and payload structures for start/result/error.  
   - Ensure these fields are optional and validated.

2. **Streaming tool events**  
   - Update formatter to emit `tool_start`, `tool_output`, and `tool_end` SSE events.  
   - Display interim tool outputs as ephemeral UI updates (consult OpenWebUI contract).

3. **Runner hook integration**  
   - Add hook invocations within `FlowRunner` for tool lifecycle transitions.  
   - Provide default hooks for logging/metrics, optionally bridging to tracing providers mentioned in docs (e.g., OpenTelemetry).

4. **Sample flow instrumentation**  
   - Instrument at least one LangGraph example to emit the new tool events.  
   - Capture before/after transcripts in documentation to illustrate behaviour.

**Exit criteria:** Tool invocations produce structured streaming updates and can be traced via hooks; sample flows demonstrate the experience.

---

## Milestone M4 – Reliability & Automation

1. **Pipeline adapter test harness**  
   - Build fixtures to simulate FlowRunner responses (sync + streaming) and assert SSE output matches expectations.  
   - Cover error propagation, status-only events, and tool lifecycle paths.

2. **Session backend tests**  
   - Add integration tests against Redis (use test container) and unit tests with fakes.  
   - Validate reconnection, TTL enforcement, and serialization boundaries.

3. **CI integration**  
   - Update workflows (`.github/workflows/`) to run new tests, provisioning Redis services as needed.  
   - Add linting rule to ensure formatter schemas stay in sync with metadata models.

4. **Error taxonomy & surfacing**  
   - Introduce structured error codes in `FlowOutput.metadata` (e.g., `error_code`, `error_type`).  
   - Update formatter to emit descriptive SSE error events and adjust docs accordingly.

**Exit criteria:** Automated suite runs in CI, failures produce actionable error metadata, and all new metadata paths are covered by tests.

---

## Milestone M5 – Documentation & Adoption

1. **Quickstart & operations guide refresh**  
   - Update `docs/openwebui_pipelines_quickstart.md` with new valves, backend requirements, and troubleshooting steps.  
   - Add instructions for enabling reasoning/tool event visualizations in OpenWebUI.

2. **Architecture deep-dive**  
   - Create a new doc (e.g., `docs/openwebui_pipeline_architecture.md`) summarizing the runtime topology, event schema, and hook system.  
   - Include sequence diagrams for streaming flows and tool interactions.

3. **Migration checklist**  
   - Provide a checklist for flow authors updating to the new metadata schema (status -> event types, tool telemetry).  
   - Highlight breaking changes, required fields, and testing tips.

4. **Rollout tracking**  
   - Maintain a lightweight status table in this roadmap with completion dates and owners once work begins.  
   - Optionally integrate with project management tooling via weekly updates.

**Exit criteria:** Documentation reflects the post-refresh architecture, onboarding instructions are current, and teams have guidance for adopting the new event semantics.

---

## Additional Considerations

- **Backward Compatibility:** Treat all new metadata fields as additive; pipelines must gracefully handle flows that emit legacy-only metadata until migrations complete.
- **Performance Monitoring:** Consider capturing timing metadata (per chunk latency, total run time) alongside tool events for future UI visualizations.
- **Security Review:** Persistent session backends introduce new operational risk; ensure credentials are pulled from valves/env vars and document rotation practices.

This roadmap should be reviewed quarterly or when major architectural changes land. Update the "Last updated" timestamp and milestone table as progress is made.
