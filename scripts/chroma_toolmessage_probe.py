#!/usr/bin/env python3
"""Standalone probe for ToolMessage payloads before model invocation.

This script is intentionally one-off/debug oriented. It inspects LangGraph
`astream_events` to capture what is sent into `on_chat_model_start` after tool
calls, which helps diagnose collection-name merge behavior.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv

from athos.models.enums import ExecutionMode
from athos.models.flow import FlowInput
from athos.models.message import Message
from athos.models.session import FlowSession
from athos.runtime.builder import build_config, build_flow


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> str:
    return str(value)


def _flatten_messages(messages: Any) -> List[Any]:
    """Normalize langchain event message payloads into a simple list."""
    if messages is None:
        return []
    if isinstance(messages, list):
        if len(messages) == 1 and isinstance(messages[0], list):
            return list(messages[0])
        return list(messages)
    return [messages]


def _extract_tool_message_blocks(messages: Iterable[Any]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for message in messages:
        if type(message).__name__ != "ToolMessage":
            continue
        content = getattr(message, "content", None)
        blocks.append(
            {
                "tool_name": getattr(message, "name", None),
                "tool_call_id": getattr(message, "tool_call_id", None),
                "content_type": type(content).__name__,
                "content": content,
                "repr": repr(message),
            }
        )
    return blocks


async def run_probe(
    config_path: str,
    flow_name: str,
    message: str,
    attempts: int,
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    load_dotenv(".env")

    with out_path.open("w", encoding="utf-8") as out:
        for idx in range(1, attempts + 1):
            cfg = build_config(config_path)
            flow = await build_flow(flow_name, cfg)

            if not hasattr(flow, "_graph"):
                raise RuntimeError(
                    f"Flow '{flow_name}' does not expose LangGraph internals; "
                    "this probe is intended for langchain_agent flows."
                )

            if hasattr(flow, "_ensure_mcp_tools_loaded"):
                await flow._ensure_mcp_tools_loaded()  # type: ignore[attr-defined]
            if hasattr(flow, "_ensure_graph_built"):
                await flow._ensure_graph_built()  # type: ignore[attr-defined]

            session_id = f"probe_{flow_name}_{idx}_{uuid.uuid4().hex[:8]}"
            flow_input = FlowInput(
                message=Message(role="user", content=message),
                session=FlowSession(
                    session_id=session_id,
                    user_id="probe_user",
                    messages=[],
                ),
                mode=ExecutionMode.SYNC,
                metadata={},
            )
            run_config = flow._build_langgraph_config(flow_input.session.session_id)  # type: ignore[attr-defined]
            input_messages = flow._build_messages(flow_input)  # type: ignore[attr-defined]

            # Record attempt metadata first.
            out.write(
                json.dumps(
                    {
                        "ts": _ts(),
                        "attempt": idx,
                        "event": "attempt_start",
                        "flow": flow_name,
                        "session_id": session_id,
                        "message": message,
                    },
                    default=_json_default,
                )
                + "\n"
            )

            try:
                async for ev in flow._graph.astream_events(  # type: ignore[attr-defined]
                    {"messages": input_messages},
                    config=run_config,
                    version="v2",
                ):
                    event_name = ev.get("event")
                    if event_name not in {
                        "on_chat_model_start",
                        "on_chat_model_end",
                        "on_tool_start",
                        "on_tool_end",
                    }:
                        continue

                    payload: Dict[str, Any] = {
                        "ts": _ts(),
                        "attempt": idx,
                        "event": event_name,
                        "name": ev.get("name"),
                        "run_id": ev.get("run_id"),
                        "parent_ids": ev.get("parent_ids", []),
                    }

                    data = ev.get("data", {})
                    if event_name == "on_chat_model_start":
                        raw_messages = _flatten_messages((data.get("input") or {}).get("messages"))
                        payload["model_input_message_count"] = len(raw_messages)
                        payload["tool_messages"] = _extract_tool_message_blocks(raw_messages)
                        payload["model_input_preview"] = str(data.get("input"))[:2000]
                    elif event_name == "on_tool_start":
                        payload["tool_input"] = data.get("input")
                    elif event_name == "on_tool_end":
                        payload["tool_output"] = data.get("output")

                    out.write(json.dumps(payload, default=_json_default) + "\n")
            except Exception as exc:
                out.write(
                    json.dumps(
                        {
                            "ts": _ts(),
                            "attempt": idx,
                            "event": "attempt_error",
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        },
                        default=_json_default,
                    )
                    + "\n"
                )
            finally:
                if hasattr(flow, "cleanup"):
                    await flow.cleanup()

            out.write(
                json.dumps(
                    {
                        "ts": _ts(),
                        "attempt": idx,
                        "event": "attempt_end",
                    },
                    default=_json_default,
                )
                + "\n"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe ToolMessage content passed into model-start events.",
    )
    parser.add_argument(
        "--config",
        default="config/paper/cug_m1.yaml",
        help="Config file path",
    )
    parser.add_argument(
        "--flow",
        default="cug_lang_chroma_sonnet",
        help="Flow name (must be langchain_agent)",
    )
    parser.add_argument(
        "--message",
        default="What type of GPUs are in the Perlmutter supercomputer?",
        help="User input message",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=1,
        help="Number of probe attempts",
    )
    parser.add_argument(
        "--out",
        default="logs/chroma_toolmessage_probe.jsonl",
        help="JSONL output file path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        run_probe(
            config_path=args.config,
            flow_name=args.flow,
            message=args.message,
            attempts=args.attempts,
            out_path=Path(args.out),
        )
    )


if __name__ == "__main__":
    main()
