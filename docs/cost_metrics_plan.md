# Cost Metrics Tracking Implementation Plan

## Overview

Add comprehensive cost/performance metrics tracking across LangGraph and SmolAgents flows, focusing on token counts, tool calls, and latency. Integrate metrics into the
evaluation framework for per-test-case and aggregate reporting.

## Implementation Steps

1. Define Standardized Metrics Schema (NEW)

File: athos/models/metrics.py (new file)
- Create Pydantic models for cost metrics:
  - TokenUsage(input_tokens, output_tokens, total_tokens)
  - ToolCallMetrics(tool_name, count)
  - ExecutionMetrics(token_usage, tool_calls, latency_ms, step_count)
- Provides type-safe structure for FlowOutput.metadata
- Ensures consistency across frameworks

2. Update SmolAgents Flows

File: athos/frameworks/smolagents/flows/agent.py
- Add return_full_result=True to agent.run() call
- Extract result.token_usage → FlowOutput.metadata["token_usage"]
- Extract tool call summary → metadata["tool_calls"]
- Extract step count → metadata["step_count"]
- Use standardized ExecutionMetrics model

3. Update LangGraph Flows

File: athos/frameworks/langgraph/flows/agent.py
- Add token usage extraction (currently missing)
- Extract from final message: state["messages"][-1].usage_metadata
- Aggregate tool call information from agent steps
- Use standardized ExecutionMetrics model

File: athos/frameworks/langgraph/flows/chatbot.py
- Already extracts tokens, update to use standardized schema
- Ensure consistent metadata structure

4. Enhance FlowRunner

File: athos/runtime/runner.py
- In execute() method, aggregate metrics from FlowOutput.metadata
- Convert execution_time (seconds) to milliseconds for consistency
- Add aggregated metrics to FlowResult.metadata including:
  - Token usage (from flow)
  - Execution latency (from runner timing)
  - Tool calls (from flow)
- Preserve backward compatibility with flows that don't provide metrics

5. Update Evaluation Framework

File: evals/run_evaluations.py
- Enhance result collection to capture FlowResult.metadata
- Add per-test-case metrics to results dict:
  - token_usage, latency_ms, tool_calls
- Add aggregate statistics calculation:
  - Total/average/min/max tokens
  - Total/average/min/max latency
  - Tool usage distribution
- Update JSON output format to include metrics section
- Add summary report with cost metrics alongside accuracy

6. Add Tests

File: tests/models/test_metrics.py (new)
- Test metrics model validation and serialization

Files: tests/frameworks/*/test_*_flows.py
- Verify each flow populates metadata correctly
- Check token_usage, tool_calls, step_count presence
- Validate metrics schema compliance

File: tests/runtime/test_runner.py
- Verify FlowRunner aggregates metrics from FlowOutput
- Ensure latency calculation is accurate
- Test backward compatibility with metric-less flows

File: tests/test_evaluations.py (new or enhanced)
- End-to-end test of evaluation with metrics
- Verify aggregate statistics calculation

## Key Design Decisions

1. No dollar costs: Skip pricing configuration entirely per user requirements
2. Framework-agnostic schema: Standardized ExecutionMetrics model works for both frameworks
3. Backward compatible: Flows without metrics still work, metrics optional in metadata
4. Latency source: Use FlowRunner's existing wall-clock timing (already implemented)
5. Tool calls: Track tool names and counts, not full arguments (privacy/size concerns)

## Files Modified/Created

- NEW: athos/models/metrics.py
- MODIFIED: athos/frameworks/smolagents/flows/agent.py
- MODIFIED: athos/frameworks/langgraph/flows/agent.py
- MODIFIED: athos/frameworks/langgraph/flows/chatbot.py
- MODIFIED: athos/runtime/runner.py
- MODIFIED: evals/run_evaluations.py
- NEW: tests/models/test_metrics.py
- MODIFIED: tests/frameworks/*/test_*_flows.py
- MODIFIED: tests/runtime/test_runner.py

## Expected Outcome

- All flows report token usage, tool calls, and latency in standardized format
- Evaluation framework shows per-test-case and aggregate cost metrics
- Easy comparison of cost/performance across different flows and configurations
- Foundation for future observability enhancements (hooks, Prometheus metrics)

## Progress Tracking (as of 2025-11-29)

Based on a recent evaluation, here is the status of each implementation step.

**Implementation Status:**

*   **1. Define Standardized Metrics Schema:** [COMPLETED]
    *   `src/athos/models/metrics.py` has been created with the specified Pydantic models.
*   **2. Update SmolAgents Flows:** [COMPLETED]
    *   `src/athos/frameworks/smolagents/flows/agent.py`: [COMPLETED] - Metrics are being extracted.
*   **3. Update LangGraph Flows:** [COMPLETED]
    *   `src/athos/frameworks/langgraph/flows/agent.py`: [COMPLETED] - Metrics are being extracted.
    *   `src/athos/frameworks/langgraph/flows/chatbot.py`: [COMPLETED] - Metrics are being extracted using the standardized schema.
*   **4. Enhance FlowRunner:** [COMPLETED]
    *   `src/athos/runtime/runner.py` correctly aggregates metrics from `FlowOutput` and adds latency.
*   **5. Update Evaluation Framework:** [COMPLETED]
    *   `evals/run_evaluations.py` has been updated to process, aggregate, and report metrics.

**Testing Status:**

*   **`tests/models/test_metrics.py`:** [COMPLETED]
    *   The new metrics models are well-tested.
*   **`tests/frameworks/*/test_*_flows.py`:** [INCOMPLETE]
    *   Tests for `smol_agent` flow metrics are **missing**.
    *   Tests for `langchain_agent` flow metrics are **missing**.
    *   Tests for `langgraph_chatbot` flow metrics are **missing**.
*   **`tests/runtime/test_runner.py`:** [COMPLETED]
    *   The `FlowRunner`'s metric aggregation logic is tested.
*   **`tests/test_evaluations.py`:** [INCOMPLETE]
    *   The test for the evaluation script (`test_run_evaluations.py`) does not cover the new metrics functionality.

**Summary:**

The core implementation is largely in place, but there is a significant gap in testing coverage for the new metrics functionality within the flows and the end-to-end evaluation script.
