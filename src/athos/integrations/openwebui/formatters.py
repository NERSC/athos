"""Formatting utilities for OpenWebUI streaming events."""

from __future__ import annotations

from typing import Any, Dict, List

from athos.models.flow import Artifact, FlowOutput


def format_for_openwebui(output: FlowOutput) -> Dict[str, Any]:
    """Convert a :class:`FlowOutput` into an OpenWebUI-friendly payload.

    The formatter inspects ``FlowOutput.metadata`` to determine which kind of
    Server-Sent Event should be produced.  It supports:

    * ``thinking`` updates rendered as reasoning blocks
    * tool/status notifications surfaced via ``event`` payloads
    * incremental content deltas for streaming responses
    * final content blocks with artifact rendering
    """

    metadata = output.metadata or {}
    event_type = metadata.get("event_type")

    if metadata.get("error"):
        description = metadata.get("status_message") or output.content or ""
        return {
            "event": {
                "type": "status",
                "data": {"description": description, "done": True},
            }
        }

    if event_type == "thinking":
        reasoning = output.content or metadata.get("status_message") or ""
        return {
            "choices": [
                {
                    "delta": {"reasoning_content": reasoning},
                    "finish_reason": None,
                }
            ]
        }

    if event_type in {"tool_call", "tool_result", "status"} or metadata.get(
        "status_message"
    ):
        description = metadata.get("status_message") or output.content or ""
        done = bool(metadata.get("status_done"))
        if event_type == "tool_result" and "status_done" not in metadata:
            done = True
        return {
            "event": {
                "type": "status",
                "data": {"description": description, "done": done},
            }
        }

    if metadata.get("streaming") and metadata.get("chunk"):
        return {
            "choices": [
                {
                    "delta": {"content": output.content},
                    "finish_reason": None,
                }
            ]
        }

    content = output.content or ""
    artifacts_markdown = _render_artifact_markdown(output.artifacts)
    if artifacts_markdown:
        content = f"{content}{artifacts_markdown}"

    finish_reason = metadata.get("finish_reason")
    if finish_reason is None and (metadata.get("final") or not metadata.get("streaming")):
        finish_reason = "stop"

    payload: Dict[str, Any] = {
        "choices": [
            {
                "delta": {"content": content},
                "finish_reason": finish_reason,
            }
        ]
    }

    artifact_event = _render_artifact_event(output.artifacts)
    if artifact_event:
        payload["event"] = {"type": "artifacts", "data": artifact_event}

    return payload


def _render_artifact_markdown(artifacts: List[Artifact]) -> str:
    """Render artifacts as markdown snippets appended to the response."""

    pieces: List[str] = []
    for artifact in artifacts:
        title = artifact.display_name or artifact.metadata.get("title") or artifact.type
        if artifact.type == "image" and artifact.path:
            pieces.append(f"\n\n![{title}]({artifact.path})")
        elif artifact.type == "file" and artifact.path:
            pieces.append(f"\n\n📄 [{title}]({artifact.path})")
        elif artifact.type == "link" and artifact.data:
            pieces.append(f"\n\n🔗 [{title}]({artifact.data})")
    return "".join(pieces)


def _render_artifact_event(artifacts: List[Artifact]) -> List[Dict[str, Any]]:
    """Convert artifacts into OpenWebUI event payloads."""

    entries: List[Dict[str, Any]] = []
    for artifact in artifacts:
        uri = artifact.path or artifact.data
        if not uri:
            continue

        entry: Dict[str, Any] = {"type": artifact.type, "uri": uri}
        title = artifact.display_name or artifact.metadata.get("title")
        if title:
            entry["title"] = title
        if artifact.metadata:
            entry["metadata"] = artifact.metadata
        entries.append(entry)
    return entries
