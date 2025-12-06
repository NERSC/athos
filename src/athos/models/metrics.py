"""
Cost and performance metrics models for ATHOS flows.

These models provide a standardized schema for tracking execution metrics
across different agent frameworks (LangGraph, SmolAgents, etc.).
"""

from typing import List, Optional
from pydantic import BaseModel, Field, computed_field


class TokenUsage(BaseModel):
    """Token usage metrics for LLM calls.

    Attributes:
        input_tokens: Number of tokens in the input/prompt
        output_tokens: Number of tokens in the output/completion
        total_tokens: Total tokens used (computed)
    """
    input_tokens: int = Field(ge=0, description="Number of input/prompt tokens")
    output_tokens: int = Field(ge=0, description="Number of output/completion tokens")

    @computed_field
    @property
    def total_tokens(self) -> int:
        """Total tokens is the sum of input and output tokens."""
        return self.input_tokens + self.output_tokens

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add two TokenUsage instances together for aggregation."""
        if not isinstance(other, TokenUsage):
            raise TypeError(f"Cannot add TokenUsage and {type(other)}")
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )


class ToolCallInfo(BaseModel):
    """Information about a tool call.

    Attributes:
        name: Name of the tool that was called
        call_count: Number of times this tool was invoked (default 1)
    """
    name: str = Field(description="Tool name")
    call_count: int = Field(default=1, ge=1, description="Number of invocations")


class ExecutionMetrics(BaseModel):
    """Comprehensive execution metrics for a flow run.

    This model aggregates all cost and performance metrics for a single
    flow execution, providing a standardized interface across frameworks.

    Attributes:
        token_usage: Token counts (input/output/total)
        latency_ms: Execution time in milliseconds
        tool_calls: List of tool calls made during execution
        step_count: Number of agent steps/iterations (for multi-step agents)
        model_name: Name/ID of the model used
    """
    token_usage: Optional[TokenUsage] = Field(
        default=None,
        description="Token usage metrics (if available from the model)"
    )
    latency_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Execution time in milliseconds"
    )
    tool_calls: List[ToolCallInfo] = Field(
        default_factory=list,
        description="Tools invoked during execution"
    )
    step_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of agent steps (for multi-step flows)"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Model identifier"
    )

    def merge_tool_calls(self, tool_calls: List[ToolCallInfo]) -> None:
        """Merge additional tool calls into this metrics object.

        If a tool with the same name already exists, increment its call_count.
        Otherwise, add it to the list.

        Args:
            tool_calls: List of tool calls to merge
        """
        tool_map = {tc.name: tc for tc in self.tool_calls}

        for new_call in tool_calls:
            if new_call.name in tool_map:
                tool_map[new_call.name].call_count += new_call.call_count
            else:
                tool_map[new_call.name] = new_call

        self.tool_calls = list(tool_map.values())

    def to_dict(self) -> dict:
        """Convert to dictionary for FlowOutput.metadata.

        Returns a JSON-serializable dictionary representation.
        """
        return self.model_dump(mode="json", exclude_none=True)

    @classmethod
    def from_metadata(cls, metadata: dict) -> Optional["ExecutionMetrics"]:
        """Create ExecutionMetrics from FlowOutput.metadata dict.

        Args:
            metadata: Metadata dictionary from FlowOutput

        Returns:
            ExecutionMetrics instance if metrics data is present, None otherwise
        """
        if not metadata:
            return None

        # Extract token usage if present
        token_usage = None
        if "token_usage" in metadata:
            token_data = metadata["token_usage"]
            if isinstance(token_data, dict):
                token_usage = TokenUsage(**token_data)

        # Extract tool calls if present
        tool_calls = []
        if "tool_calls" in metadata:
            tool_data = metadata["tool_calls"]
            if isinstance(tool_data, list):
                for tc in tool_data:
                    if isinstance(tc, dict):
                        tool_calls.append(ToolCallInfo(**tc))

        # Extract other fields
        return cls(
            token_usage=token_usage,
            latency_ms=metadata.get("latency_ms"),
            tool_calls=tool_calls,
            step_count=metadata.get("step_count"),
            model_name=metadata.get("model_name"),
        )


def aggregate_metrics(metrics_list: List[ExecutionMetrics]) -> ExecutionMetrics:
    """Aggregate multiple ExecutionMetrics into a single summary.

    Args:
        metrics_list: List of ExecutionMetrics to aggregate

    Returns:
        ExecutionMetrics with summed/averaged values
    """
    if not metrics_list:
        return ExecutionMetrics()

    # Aggregate token usage
    total_token_usage = None
    token_usages = [m.token_usage for m in metrics_list if m.token_usage]
    if token_usages:
        total_token_usage = token_usages[0]
        for usage in token_usages[1:]:
            total_token_usage = total_token_usage + usage

    # Aggregate latency (sum)
    total_latency = sum(
        m.latency_ms for m in metrics_list if m.latency_ms is not None
    )

    # Aggregate tool calls
    all_tool_calls: List[ToolCallInfo] = []
    for m in metrics_list:
        all_tool_calls.extend(m.tool_calls)

    # Merge duplicate tool calls
    tool_map = {}
    for tc in all_tool_calls:
        if tc.name in tool_map:
            tool_map[tc.name].call_count += tc.call_count
        else:
            tool_map[tc.name] = ToolCallInfo(name=tc.name, call_count=tc.call_count)

    # Sum step counts
    total_steps = sum(
        m.step_count for m in metrics_list if m.step_count is not None
    )

    return ExecutionMetrics(
        token_usage=total_token_usage,
        latency_ms=total_latency if total_latency > 0 else None,
        tool_calls=list(tool_map.values()),
        step_count=total_steps if total_steps > 0 else None,
    )
