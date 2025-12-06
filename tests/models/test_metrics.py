"""Tests for cost/performance metrics models."""

import pytest
from athos.models.metrics import (
    TokenUsage,
    ToolCallInfo,
    ExecutionMetrics,
    aggregate_metrics,
)


class TestTokenUsage:
    """Test TokenUsage model."""

    def test_total_tokens_computed(self):
        """Test that total_tokens is automatically computed."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_addition(self):
        """Test adding two TokenUsage instances."""
        usage1 = TokenUsage(input_tokens=100, output_tokens=50)
        usage2 = TokenUsage(input_tokens=200, output_tokens=75)
        combined = usage1 + usage2

        assert combined.input_tokens == 300
        assert combined.output_tokens == 125
        assert combined.total_tokens == 425

    def test_addition_type_error(self):
        """Test that adding non-TokenUsage raises TypeError."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        with pytest.raises(TypeError):
            _ = usage + 42

    def test_serialization(self):
        """Test serialization to dict."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        data = usage.model_dump()

        assert data["input_tokens"] == 100
        assert data["output_tokens"] == 50
        assert data["total_tokens"] == 150


class TestToolCallInfo:
    """Test ToolCallInfo model."""

    def test_default_call_count(self):
        """Test that call_count defaults to 1."""
        tool = ToolCallInfo(name="search")
        assert tool.call_count == 1

    def test_custom_call_count(self):
        """Test custom call_count."""
        tool = ToolCallInfo(name="search", call_count=5)
        assert tool.call_count == 5


class TestExecutionMetrics:
    """Test ExecutionMetrics model."""

    def test_empty_metrics(self):
        """Test creating empty metrics."""
        metrics = ExecutionMetrics()
        assert metrics.token_usage is None
        assert metrics.latency_ms is None
        assert metrics.tool_calls == []
        assert metrics.step_count is None
        assert metrics.model_name is None

    def test_full_metrics(self):
        """Test metrics with all fields populated."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        tool_calls = [
            ToolCallInfo(name="search", call_count=2),
            ToolCallInfo(name="calculator", call_count=1),
        ]

        metrics = ExecutionMetrics(
            token_usage=usage,
            latency_ms=1234.5,
            tool_calls=tool_calls,
            step_count=3,
            model_name="gpt-4",
        )

        assert metrics.token_usage == usage
        assert metrics.latency_ms == 1234.5
        assert len(metrics.tool_calls) == 2
        assert metrics.step_count == 3
        assert metrics.model_name == "gpt-4"

    def test_merge_tool_calls_new(self):
        """Test merging tool calls that don't exist yet."""
        metrics = ExecutionMetrics(
            tool_calls=[ToolCallInfo(name="search", call_count=1)]
        )

        new_calls = [ToolCallInfo(name="calculator", call_count=2)]
        metrics.merge_tool_calls(new_calls)

        assert len(metrics.tool_calls) == 2
        assert any(tc.name == "search" and tc.call_count == 1 for tc in metrics.tool_calls)
        assert any(tc.name == "calculator" and tc.call_count == 2 for tc in metrics.tool_calls)

    def test_merge_tool_calls_existing(self):
        """Test merging tool calls that already exist (increments count)."""
        metrics = ExecutionMetrics(
            tool_calls=[ToolCallInfo(name="search", call_count=1)]
        )

        new_calls = [ToolCallInfo(name="search", call_count=2)]
        metrics.merge_tool_calls(new_calls)

        assert len(metrics.tool_calls) == 1
        assert metrics.tool_calls[0].name == "search"
        assert metrics.tool_calls[0].call_count == 3

    def test_to_dict(self):
        """Test conversion to dictionary."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        metrics = ExecutionMetrics(
            token_usage=usage,
            latency_ms=1234.5,
            tool_calls=[ToolCallInfo(name="search")],
            step_count=2,
            model_name="gpt-4",
        )

        data = metrics.to_dict()

        assert "token_usage" in data
        assert data["token_usage"]["input_tokens"] == 100
        assert data["latency_ms"] == 1234.5
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["name"] == "search"
        assert data["step_count"] == 2
        assert data["model_name"] == "gpt-4"

    def test_to_dict_excludes_none(self):
        """Test that to_dict excludes None values."""
        metrics = ExecutionMetrics(latency_ms=100.0)
        data = metrics.to_dict()

        assert "latency_ms" in data
        assert "token_usage" not in data
        assert "step_count" not in data
        assert "model_name" not in data

    def test_from_metadata_empty(self):
        """Test from_metadata with empty dict returns None."""
        metrics = ExecutionMetrics.from_metadata({})
        # Empty dict has no metrics data, so should return None
        assert metrics is None

    def test_from_metadata_none(self):
        """Test from_metadata with None returns None."""
        metrics = ExecutionMetrics.from_metadata(None)
        assert metrics is None

    def test_from_metadata_with_token_usage(self):
        """Test from_metadata with token usage."""
        metadata = {
            "token_usage": {
                "input_tokens": 100,
                "output_tokens": 50,
            }
        }

        metrics = ExecutionMetrics.from_metadata(metadata)
        assert metrics is not None
        assert metrics.token_usage is not None
        assert metrics.token_usage.input_tokens == 100
        assert metrics.token_usage.output_tokens == 50

    def test_from_metadata_with_tool_calls(self):
        """Test from_metadata with tool calls."""
        metadata = {
            "tool_calls": [
                {"name": "search", "call_count": 2},
                {"name": "calculator", "call_count": 1},
            ]
        }

        metrics = ExecutionMetrics.from_metadata(metadata)
        assert metrics is not None
        assert len(metrics.tool_calls) == 2
        assert metrics.tool_calls[0].name == "search"
        assert metrics.tool_calls[0].call_count == 2

    def test_from_metadata_full(self):
        """Test from_metadata with all fields."""
        metadata = {
            "token_usage": {"input_tokens": 100, "output_tokens": 50},
            "latency_ms": 1234.5,
            "tool_calls": [{"name": "search", "call_count": 1}],
            "step_count": 3,
            "model_name": "gpt-4",
        }

        metrics = ExecutionMetrics.from_metadata(metadata)
        assert metrics is not None
        assert metrics.token_usage.total_tokens == 150
        assert metrics.latency_ms == 1234.5
        assert len(metrics.tool_calls) == 1
        assert metrics.step_count == 3
        assert metrics.model_name == "gpt-4"


class TestAggregateMetrics:
    """Test aggregate_metrics function."""

    def test_empty_list(self):
        """Test aggregating empty list."""
        result = aggregate_metrics([])
        assert result.token_usage is None
        assert result.latency_ms is None
        assert result.tool_calls == []

    def test_single_metrics(self):
        """Test aggregating single metrics."""
        metrics = ExecutionMetrics(
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            latency_ms=1000.0,
        )

        result = aggregate_metrics([metrics])
        assert result.token_usage.input_tokens == 100
        assert result.token_usage.output_tokens == 50
        assert result.latency_ms == 1000.0

    def test_multiple_metrics(self):
        """Test aggregating multiple metrics."""
        metrics1 = ExecutionMetrics(
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            latency_ms=1000.0,
            step_count=2,
        )
        metrics2 = ExecutionMetrics(
            token_usage=TokenUsage(input_tokens=200, output_tokens=75),
            latency_ms=1500.0,
            step_count=3,
        )

        result = aggregate_metrics([metrics1, metrics2])
        assert result.token_usage.input_tokens == 300
        assert result.token_usage.output_tokens == 125
        assert result.token_usage.total_tokens == 425
        assert result.latency_ms == 2500.0
        assert result.step_count == 5

    def test_aggregate_tool_calls(self):
        """Test aggregating tool calls across metrics."""
        metrics1 = ExecutionMetrics(
            tool_calls=[
                ToolCallInfo(name="search", call_count=2),
                ToolCallInfo(name="calculator", call_count=1),
            ]
        )
        metrics2 = ExecutionMetrics(
            tool_calls=[
                ToolCallInfo(name="search", call_count=1),
                ToolCallInfo(name="writer", call_count=3),
            ]
        )

        result = aggregate_metrics([metrics1, metrics2])
        assert len(result.tool_calls) == 3

        # Find each tool and check count
        search_tool = next(tc for tc in result.tool_calls if tc.name == "search")
        assert search_tool.call_count == 3

        calc_tool = next(tc for tc in result.tool_calls if tc.name == "calculator")
        assert calc_tool.call_count == 1

        writer_tool = next(tc for tc in result.tool_calls if tc.name == "writer")
        assert writer_tool.call_count == 3

    def test_aggregate_partial_metrics(self):
        """Test aggregating metrics where some have None values."""
        metrics1 = ExecutionMetrics(
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            latency_ms=1000.0,
        )
        metrics2 = ExecutionMetrics(
            latency_ms=500.0,
        )
        metrics3 = ExecutionMetrics(
            token_usage=TokenUsage(input_tokens=50, output_tokens=25),
        )

        result = aggregate_metrics([metrics1, metrics2, metrics3])

        # Token usage only from metrics1 and metrics3
        assert result.token_usage.input_tokens == 150
        assert result.token_usage.output_tokens == 75

        # Latency from metrics1 and metrics2
        assert result.latency_ms == 1500.0
