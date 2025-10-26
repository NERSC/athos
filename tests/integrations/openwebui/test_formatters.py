"""Tests for OpenWebUI formatting helpers."""

from athos.integrations.openwebui.formatters import format_for_openwebui
from athos.models.flow import Artifact, FlowOutput


def test_thinking_event_formats_reasoning_content() -> None:
    output = FlowOutput(content="Planning next step...", metadata={"event_type": "thinking"})

    event = format_for_openwebui(output)

    assert "choices" in event
    choice = event["choices"][0]
    assert choice["delta"]["reasoning_content"] == "Planning next step..."
    assert choice["finish_reason"] is None


def test_tool_status_event_uses_status_message() -> None:
    output = FlowOutput(
        content="",
        metadata={"event_type": "tool_call", "status_message": "🔧 Using search tool"},
    )

    event = format_for_openwebui(output)

    assert event == {
        "event": {
            "type": "status",
            "data": {"description": "🔧 Using search tool", "done": False},
        }
    }


def test_artifact_rendering_adds_markdown_and_event_payload() -> None:
    artifacts = [
        Artifact(type="image", path="https://example.com/chart.png", display_name="chart"),
        Artifact(type="file", path="https://example.com/report.pdf", display_name="report"),
        Artifact(type="link", data="https://example.com/docs", display_name="docs"),
    ]
    output = FlowOutput(content="Analysis complete.", artifacts=artifacts, metadata={"final": True})

    event = format_for_openwebui(output)

    choice = event["choices"][0]
    content = choice["delta"]["content"]
    assert "![chart](https://example.com/chart.png)" in content
    assert "📄 [report](https://example.com/report.pdf)" in content
    assert "🔗 [docs](https://example.com/docs)" in content

    assert event["event"] == {
        "type": "artifacts",
        "data": [
            {"type": "image", "uri": "https://example.com/chart.png", "title": "chart"},
            {"type": "file", "uri": "https://example.com/report.pdf", "title": "report"},
            {"type": "link", "uri": "https://example.com/docs", "title": "docs"},
        ],
    }


def test_chunk_events_stream_as_content_delta() -> None:
    output = FlowOutput(content="partial ", metadata={"streaming": True, "chunk": True})

    event = format_for_openwebui(output)

    assert event["choices"][0]["delta"] == {"content": "partial "}
    assert event["choices"][0]["finish_reason"] is None


def test_finish_reason_prefers_metadata_and_defaults_to_stop() -> None:
    explicit = FlowOutput(
        content="Done.",
        metadata={"final": True, "finish_reason": "tool_calls"},
    )
    fallback = FlowOutput(content="Complete.", metadata={"final": True})

    explicit_event = format_for_openwebui(explicit)
    fallback_event = format_for_openwebui(fallback)

    assert explicit_event["choices"][0]["finish_reason"] == "tool_calls"
    assert fallback_event["choices"][0]["finish_reason"] == "stop"
