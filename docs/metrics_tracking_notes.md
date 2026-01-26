## Metrics Tracking Notes

Context
- This note captures design issues and follow-up work for metrics tracking added on cost-metrics-2.
- Primary goals are consistent token usage extraction, tool call reporting, and latency metadata.

Issues Identified
- Inconsistent normalization: token usage/tool call coercion lives in multiple locations (flow-level helpers + `ExecutionMetrics`), which risks drift.
- Overly defensive payload handling: some helpers accept broad shapes that do not match current, pinned LangChain/SmolAgents versions.
- Streaming semantics: LangChain agent streaming currently captures token usage once from the first chunk, not by aggregating completed messages (updates).

Decisions (Agreed)
- Prefer strict typing based on currently supported library versions; reduce defensive handling where it does not add value.
- Align streaming metrics with execute() semantics by aggregating over completed messages (via stream_mode "updates").

Follow-Up Work
- Consolidate normalization into a single module (likely `src/athos/models/metrics.py`) and remove duplicate helpers from flow code.
- Simplify tool call extraction to strict, known types; remove map/attr fallback logic where not needed.

Completed
- Consolidated normalization into framework adapters and removed duplicate helpers from flow code.
- Updated LangChain agent streaming to aggregate token usage from completed messages in updates.

Open Questions
- Do we need a compatibility shim for older provider payloads, or can we rely on current pinned versions?
- Should `ExecutionMetrics` accept additional fields (e.g., prompt cache hits) in a forward-compatible way?
