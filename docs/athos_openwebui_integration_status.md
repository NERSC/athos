# ATHOS ↔ OpenWebUI Integration Status Report

_Last updated: 2025-10-20 15:30 UTC_

## Summary
- **Integration phase**: Milestone 1 — Core Runtime Foundation.
- **Overall status**: On track.
- **Recent highlights**: Core runtime model package added with unit coverage per Task 1.1.
- **Upcoming focus**: Design and implement the `SessionStore` abstraction (Task 1.2) to unlock Runner development.

## Milestone & Task Progress

| Milestone | Task | Description | Status | Notes |
| --- | --- | --- | --- | --- |
| 1. Core Runtime Foundation | 1.1 | Create models package (`athos.models`) and supporting tests. | ✅ Complete | Models merged to `work` branch with serialization & state-management coverage.
| 1. Core Runtime Foundation | 1.2 | Create SessionStore abstraction and in-memory implementation. | ⏳ In Progress (Not Started) | Awaiting design confirmation on async API boundaries and persistence requirements.
| 1. Core Runtime Foundation | 1.3 | Update BaseFlow interface to consume new models. | ⏳ Not Started | Blocked on Task 1.2 to finalize session handling contract.
| 1. Core Runtime Foundation | 1.4 | Implement basic FlowRunner orchestration. | ⏳ Not Started | Dependent on Tasks 1.2–1.3.
| 2. Runtime Compatibility | 2.1 | Create compatibility shim for legacy flows. | ⏳ Not Started | Will revisit after FlowRunner skeleton stabilizes.
| 2. Runtime Compatibility | 2.2 | LangGraph translation utilities. | ⏳ Not Started | Requires Runner streaming semantics (Milestone 1 completion).
| 2. Runtime Compatibility | 2.3 | Migrate LangGraph chatbot flow to new interfaces. | ⏳ Not Started | Pending translation utilities.
| 2. Runtime Compatibility | 2.4 | Update CLI to use runner. | ⏳ Not Started | Requires Runner and compatibility layers.
| 3. OpenWebUI Integration | 3.1 | Pipeline module bridging Runner ↔ OpenWebUI. | ⏳ Not Started | Scheduled post-Milestone 2.
| 3. OpenWebUI Integration | 3.2 | Deployment configuration & docs. | ⏳ Not Started | Post-integration hardening.
| 5. Enhancements | 5.1 | LangGraph ReAct agent streaming enhancements. | ⏳ Not Started | Requires baseline pipeline to be operational.
| 5. Enhancements | 5.2 | OpenWebUI event formatter. | ⏳ Not Started | Blocked by Milestones 2–3 completion.

## Issues & Risks
- **Session persistence contract**: Need alignment on whether session state updates remain synchronous or leverage background persistence. Decision impacts design of `SessionStore.save` signature.
- **Test coverage scope**: Additional property-based or regression tests may be required once Runner interactions are implemented to ensure backward compatibility with legacy flows.

## Feedback & Recommendations
- Consider introducing `typing.TypedDict` structures for conversation message entries to improve discoverability and static analysis when flows interact with `FlowSession.messages`.
- Evaluate whether `FlowOutput.artifacts` should support lazy-loading handles (e.g., callables, URIs) for large binary payloads before finalizing Runner streaming behavior.
- Document serialization expectations for `FlowSession.state` to ensure eventual persistence stores (e.g., Redis) can operate without extra adapters.

## Next Steps
1. Prototype `SessionStore` interface (Task 1.2) with async context handling and confirm usage patterns with Runner design doc owners.
2. Draft BaseFlow updates (Task 1.3) once session lifecycle semantics are approved.
3. Begin outlining FlowRunner execution lifecycle to anticipate integration with OpenWebUI pipeline contract.
