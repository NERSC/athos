# ATHOS ↔ OpenWebUI Integration Status Report

_Last updated: 2025-10-20 19:45 UTC_

## Summary
- **Integration phase**: Milestone 1 — Core Runtime Foundation.
- **Overall status**: On track.
- **Recent highlights**: SessionStore abstraction merged with concurrency-safe in-memory backend (Task 1.2), BaseFlow interface upgraded to structured models (Task 1.3), and FlowRunner orchestration implemented with caching + error handling (Task 1.4).
- **Upcoming focus**: Design and implement legacy compatibility adapter (Task 2.1).

## Milestone & Task Progress

| Milestone | Task | Description | Status | Notes |
| --- | --- | --- | --- | --- |
| 1. Core Runtime Foundation | 1.1 | Create models package (`athos.models`) and supporting tests. | ✅ Complete | Models merged to `work` branch with serialization & state-management coverage. |
| 1. Core Runtime Foundation | 1.2 | Create SessionStore abstraction and in-memory implementation. | ✅ Complete | Async interface finalized with atomic in-memory reference implementation and coverage. |
| 1. Core Runtime Foundation | 1.3 | Update BaseFlow interface to consume new models. | ✅ Complete | BaseFlow now consumes `FlowInput`/`FlowOutput`, supports streaming hooks, and includes lifecycle methods. |
| 1. Core Runtime Foundation | 1.4 | Implement basic FlowRunner orchestration. | ✅ Complete | FlowRunner manages sessions, caching, error handling, and has unit tests. |
| 2. Runtime Compatibility | 2.1 | Create compatibility shim for legacy flows. | ⏳ Not Started | Will revisit after FlowRunner skeleton stabilizes. |
| 2. Runtime Compatibility | 2.2 | LangGraph translation utilities. | ⏳ Not Started | Requires Runner streaming semantics (Milestone 1 completion). |
| 2. Runtime Compatibility | 2.3 | Migrate LangGraph chatbot flow to new interfaces. | ⏳ Not Started | Pending translation utilities. |
| 2. Runtime Compatibility | 2.4 | Update CLI to use runner. | ⏳ Not Started | Requires Runner and compatibility layers. |
| 3. OpenWebUI Integration | 3.1 | Pipeline module bridging Runner ↔ OpenWebUI. | ⏳ Not Started | Scheduled post-Milestone 2. |
| 3. OpenWebUI Integration | 3.2 | Deployment configuration & docs. | ⏳ Not Started | Post-integration hardening. |
| 5. Enhancements | 5.1 | LangGraph ReAct agent streaming enhancements. | ⏳ Not Started | Requires baseline pipeline to be operational. |
| 5. Enhancements | 5.2 | OpenWebUI event formatter. | ⏳ Not Started | Blocked by Milestones 2–3 completion. |

## Issues & Risks
- **Session persistence contract**: Validate atomic semantics scale to distributed backends (e.g., Redis) before Task 2.1 to avoid diverging APIs.
- **Test coverage scope**: Additional property-based or regression tests may be required once Runner interactions are implemented to ensure backward compatibility with legacy flows.

## Feedback & Recommendations
- Consider introducing `typing.TypedDict` structures for conversation message entries to improve discoverability and static analysis when flows interact with `FlowSession.messages`.
- Evaluate whether `FlowOutput.artifacts` should support lazy-loading handles. See [Artifact Handling Strategy](lazy_loading_artifacts.md) for details.
- Document serialization expectations for `FlowSession.state`. See [FlowSession State Serialization Requirements](state_serialization_requirements.md) for details.
- **CLI**: Consider enabling session resume in the main CLI once a persistent session store is implemented.
- **Examples**: The example scripts in `src/athos/examples` should be updated to reflect the new runtime design and APIs.
- **Evaluation Framework**: The evaluation framework will require development work to leverage the new runtime, which is not currently in the plan. This presents an opportunity to improve the evaluation capabilities.

## Next Steps
1. Define compatibility adapter requirements and ergonomics for legacy flows (Task 2.1).
2. Document expectations for future persistence backends (Redis, SQL) building on the SessionStore interface.
3. Identify regression scenarios for legacy flows to inform upcoming compatibility layer (Task 2.1).
