# Evaluation Metrics Reporting Plan

This document describes a staged plan to extend the evaluation pipeline to report
token usage and latency for ATHOS flows. Pricing/costs are explicitly out of scope.

## Goals
- Capture standardized latency (`latency_ms`) and token usage per evaluation case.
- Preserve existing scoring/accuracy outputs.
- Produce rollups for easy comparison across flows and datasets.
- Land changes in stages, starting with a FlowRunner migration.

## Current State (as of 2026-01-30)
- `evals/run_evaluations.py` builds flows and calls `flow.execute(...)` directly.
- Metrics already exist in flow metadata (`token_usage`, `tool_calls`) and are normalized
  in `src/athos/models/metrics.py`.
- `FlowRunner.execute(...)` attaches `latency_ms` and normalizes metrics metadata.

## Stage 1: Migrate Eval Execution to FlowRunner

### Scope
- Replace direct flow execution in `evals/run_evaluations.py` with `FlowRunner.execute(...)`.
- Keep current CLI and output structure intact for scoring results.
- Ensure session/workspace creation behavior remains the same or is a safe equivalent.

### Implementation Steps
1. Instantiate a single `FlowRunner` with the loaded config:
   - `runner = FlowRunner(cfg)`
2. For each test case, call:
   - `result = await runner.execute(flow_name, message, session_id, user_id, mode=ExecutionMode.SYNC, interface="evaluation")`
3. Replace `output = await flow.execute(...)` with `result.output` and `result.metadata`.
4. Preserve `response` extraction:
   - `response = result.output.content if result.output else f"Error ..."`
5. Keep cleanup logic:
   - `await runner.cleanup()` at the end (instead of per-flow cleanup).

### Files
- `evals/run_evaluations.py`

### Expected Outcome
- Evaluations still run with scores/accuracy unchanged.
- `FlowResult.metadata` now contains `latency_ms` and normalized metrics.

### Acceptance Criteria
- Evaluation outputs remain functionally equivalent (scores/feedback unchanged).
- No regressions in evaluation flow selection or dataset loading.
- FlowRunner executes without changing evaluator model behavior.

## Stage 2: Record Per-Case Metrics

### Scope
- Add a `metrics` block per test case in the results JSON.
- Include `latency_ms`, `token_usage`, and `tool_calls` where available.

### Implementation Steps
1. Convert `FlowResult.metadata` to `ExecutionMetrics`:
   - `metrics = ExecutionMetrics.from_output_metadata(result.metadata)`
2. Serialize metrics into the per-case result entry:
   - `metrics_dict = metrics.to_metadata()` if metrics else `{"latency_ms": ...}`.
3. Store metrics under a `metrics` key in each result entry.

### Files
- `evals/run_evaluations.py`

### Acceptance Criteria
- Each case result includes a `metrics` section.
- `latency_ms` is present for all cases.
- Token usage appears when provided by the flow.

## Stage 3: Aggregate Dataset/Flow Metrics

### Scope
- Add rollups at `flow -> dataset` level.
- Report latency statistics and token totals/averages.

### Proposed Rollups
- `avg_latency_ms`, `p50_latency_ms`, `p90_latency_ms`
- `total_input_tokens`, `total_output_tokens`, `total_tokens`
- `avg_total_tokens`
- `tool_calls_total`, `tool_calls_unique` (optional)

### Implementation Steps
1. Accumulate per-case metrics during the dataset loop.
2. Compute basic stats at the end of each dataset.
3. Store rollups under `summary` in the JSON output.

### Files
- `evals/run_evaluations.py`

### Acceptance Criteria
- Summary block exists for each dataset.
- Rollups are consistent with per-case metrics.

## Stage 4: Output Schema Update (Optional)

### Scope
- Wrap output in a top-level structure for future extensions:
  - `meta` (timestamp, run parameters)
  - `flows` (nested by flow/dataset)

### Acceptance Criteria
- Backward compatibility maintained or documented if changed.

## Testing and Validation
- Run a small eval set (1 flow, 1 dataset) before/after Stage 1.
- Verify response content and evaluation scores are unchanged.
- Confirm `latency_ms` is non-null and tokens appear for supported flows.

## Out of Scope
- Pricing/cost calculations.
- Changes to model configuration.
- New metrics beyond latency and token usage.
