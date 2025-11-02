# OpenWebUI Pipeline Roadmap (2025 Q2 Refresh)

_Last updated: 2025-06-02_

## Current Snapshot

Athos now exposes flows to OpenWebUI through the `FlowRunner`-backed manifold pipeline (`integrations/openwebui/pipelines/athos_flowrunner_manifold_pipeline.py`). The adapter supports synchronous and streaming execution, translates artifacts into markdown, and respects the shared `FlowOutput` metadata contract (`streaming`, `final`, `status_message`, etc.). Sessions are still persisted in-memory, and there is only rudimentary handling for status text, tool usage, and other non-chat events.

The quickstart in `docs/openwebui_pipelines_quickstart.md` remains accurate for spinning up the current pipeline stack. This roadmap replaces the archived integration status and plan documents and should be treated as the single source of truth for OpenWebUI pipeline work moving forward.

## Milestone Overview

| Milestone | Objective | Themes |
| --- | --- | --- |
| M1. Durable Sessions | Land a Redis-backed persistent store and polish session ergonomics. | Redis backend, session UX, connection validation |
| M2. Rich Event Semantics | Extend metadata + streaming surface for reasoning, status, and structured events. | Event schema, SSE formatting, formatter utilities |
| M3. Cost Metrics & Basic Observability | Track token usage, calculate costs, and aggregate session-level statistics. | Token tracking, pricing utilities, usage aggregation |
| M4. Reliability & Automation | Establish automated coverage and harden error handling. | Tests, mocks, validation, CI integration |
| M5. Documentation & Adoption | Refresh docs, examples, and migration guidance. | Docs, quickstart updates, rollout plan |

Each milestone below lists concrete tasks with enough context for an engineer or coding agent to execute independently. Tasks are prioritized in execution order unless otherwise noted.

### Milestone Dependencies & Prioritization

- **M1 → M2 (optional sequencing):** Rich event semantics (M2) only rely on shared model updates (`FlowOutput.metadata`) and formatter plumbing inside the OpenWebUI adapter. Those changes do not depend on Redis durability, so teams can begin M2 before M1 finishes if session persistence is less urgent. Coordination is only required to ensure streaming transcripts continue to exclude hidden events once both milestones land.
- **M1 prerequisites:** Implementing the Redis store does not require schema changes elsewhere; it reuses the existing session abstraction in `FlowRunner`. No migration tooling needed since current sessions are in-memory only.
- **M2 → M3 (independent):** Cost tracking (M3) extends the metadata schema established in M2, but can proceed in parallel if metadata design is settled. Token usage tracking does not depend on event type semantics.
- **M3 → M4:** Reliability automation (M4) should include tests for usage aggregation and cost calculation utilities introduced in M3.
- **M4 covers new paths from M2 and M3:** Expect to refresh or expand tests as M2 introduces new SSE event types and M3 adds usage tracking.
- **M5 (docs) spans all milestones:** Documentation updates will trail each milestone to capture new valves, schemas, and operational steps.

---

## Milestone M1 – Durable Sessions

1. **Implement Redis `SessionStore` backend**
   - Location: `src/athos/runtime/session_store/` (create subpackage if needed).
   - Provide async CRUD mirroring the in-memory store; support configurable TTL.
   - Add valve configuration to the pipeline (`integrations/openwebui/pipelines/...`) to select backend + connection settings.

2. **Redis connection validation**
   - Add basic connectivity check in `RedisSessionStore.__init__()` that fails fast with clear error if Redis is unreachable.
   - Log warning on startup if connection is slow (>100ms).
   - Document Redis configuration and troubleshooting in quickstart (no migration tooling needed since current sessions are in-memory only).

3. **Session UX improvements**
   - Ensure history replay uses persisted sessions exclusively (audit `FlowRunner`).
   - Provide valve toggles for auto-reset, TTL, and maximum transcript length; document defaults in quickstart.

**Exit criteria:** Redis backend in production use, automated smoke test covering resume across restarts, updated quickstart instructions.

---

## Milestone M2 – Rich Event Semantics

1. **Define `FlowOutput.metadata.event_type` schema**
   - Extend models in `src/athos/models/flow.py` with typed enums for events (`chat`, `status`, `reasoning`, `tool_start`, etc.).
   - Document serialization requirements and ensure backwards compatibility.
   - Schema maps to JSON field names in SSE `data:` chunks (OpenWebUI expects `data: {json}` format, not named SSE events).

2. **Introduce OpenWebUI event formatter module**
   - Create `integrations/openwebui/formatters/events.py` to map `FlowOutput` + metadata into SSE JSON payloads.
   - Emit reasoning/status as distinct JSON fields (e.g., `{"reasoning": "...", "choices": [{"delta": {"content": ""}}]}`) following OpenAI streaming format.
   - Status and reasoning events should have empty `delta.content` to prevent transcript persistence in OpenWebUI.

3. **Update pipeline stream handling**
   - Refactor `pipe()` streaming loop to delegate formatting to the new module.
   - Use structured JSON fields to differentiate event types while maintaining `data: {json}\n\n` SSE format.
   - Ensure only events with non-empty `delta.content` are persisted to chat history.

4. **Backfill flow emitters**
   - Update representative flows (`src/athos/flows/...` or LangGraph adapters) to populate reasoning/status metadata for known steps.
   - Provide guidelines for other flow authors via docstring or developer guide snippet.

**Exit criteria:** Pipeline produces distinct JSON payloads for chat, status, and reasoning content within standard SSE `data:` chunks; transcripts remain clean; documentation explains the event taxonomy and JSON field specifications.

---

## Milestone M3 – Cost Metrics & Basic Observability

1. **Token usage tracking**
   - Extend metadata schema with standardized `usage` structure: `{"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}`.
   - Add `model_id` and `provider` fields to support multi-model cost attribution.
   - Update flows to populate usage metadata from model API responses (LangGraph, SmolAgents).

2. **Cost calculation utilities**
   - Create `athos/utils/cost_tracking.py` with pricing data for common models (OpenAI, Anthropic, CBORG).
   - Provide `calculate_cost(usage: dict, model_id: str) -> float` helper.
   - Support environment-variable overrides for custom pricing (`ATHOS_PRICING_CONFIG_PATH`).

3. **Usage aggregation in FlowRunner**
   - Track cumulative token usage per session in `FlowSession.metadata["usage_stats"]`.
   - Emit usage data in final `FlowOutput.metadata` for both sync and streaming executions.
   - Add optional logging of usage statistics at completion (controlled by valve/config).

4. **OpenWebUI integration**
   - Ensure pipeline's `_build_stream_final()` includes `usage` in SSE payload (already partially implemented at line 446).
   - Add optional valve to display cost estimates in UI (via metadata or status messages).
   - Document usage tracking in quickstart with example of enabling cost logging.

**Exit criteria:** All flows emit standardized token usage, FlowRunner aggregates session-level stats, pipeline surfaces usage to OpenWebUI, documentation explains cost tracking setup.

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
