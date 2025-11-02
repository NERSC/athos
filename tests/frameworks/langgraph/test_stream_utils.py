from __future__ import annotations

from athos.frameworks.langgraph.flows._stream_utils import (
    _TOOL_RESULT_MAX_LENGTH,
    _coerce_tool_message_content,
)


def test_coerce_tool_message_content_prefers_answer_field():
    content = {
        "answer": "Here is the concise answer.",
        "results": [
            {"title": "Ignored", "content": "This should not appear"},
        ],
    }

    result = _coerce_tool_message_content(content)

    assert result == "Here is the concise answer."


def test_coerce_tool_message_content_summarizes_results_list():
    content = {
        "results": [
            {"title": "Item A", "content": "Snippet A"},
            {"title": "Item B", "content": "Snippet B"},
            {"title": "Item C", "content": "Snippet C"},
            {"title": "Item D", "content": "Snippet D"},
        ]
    }

    result = _coerce_tool_message_content(content)

    assert result.count("\n") == 2  # Only the first three entries are included
    assert "Item A" in result and "Snippet A" in result
    assert "Item D" not in result


def test_coerce_tool_message_content_truncates_long_payloads():
    long_value = "x" * (_TOOL_RESULT_MAX_LENGTH + 100)
    content = {"results": long_value}

    result = _coerce_tool_message_content(content)

    assert len(result) == _TOOL_RESULT_MAX_LENGTH
    assert result.endswith("…")
