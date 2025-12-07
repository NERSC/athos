"""Streaming demo for the SFAPI agent using FlowRunner.stream.

Run against your config to exercise the streaming path without OpenWebUI:
    python -m athos.examples.sfapi_agent_stream --config config/config.yaml --flow lang_sfapi_agent "status of systems"
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv

from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner

# Load environment variables from .env if present
load_dotenv()


async def stream_flow(
    runner: FlowRunner,
    flow_name: str,
    message: str,
    session_id: str,
    user_id: str,
    *,
    show_metadata: bool,
    stream_stdout: bool,
) -> None:
    """Stream a single message through the flow and print chunks with metadata."""
    print(f"\n🔌 Streaming flow '{flow_name}' with message: {message!r}\n")
    async for chunk in runner.stream(
        flow_name=flow_name,
        message=message,
        session_id=session_id,
        user_id=user_id,
        interface="openwebui",  # match the OpenWebUI interface path
        metadata={"source": "sfapi_stream_demo"},
    ):
        content = chunk.content or ""
        meta: Dict[str, Any] = chunk.metadata or {}
        if stream_stdout:
            sys.stdout.write(content)
            sys.stdout.flush()
        else:
            print(f"chunk: {content}")
        if show_metadata and meta:
            # Send metadata to stderr so --raw output stays clean
            sys.stderr.write(f"\n  metadata: {meta}\n")
            sys.stderr.flush()
    if stream_stdout:
        sys.stdout.write("\n")
        sys.stdout.flush()
    print("\n✅ Stream complete\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description="ATHOS SFAPI streaming demo")
    parser.add_argument(
        "message",
        nargs="?",
        default="What systems are available at NERSC and what are their statuses?",
        help="User message to send to the flow",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration YAML file",
    )
    parser.add_argument(
        "--flow",
        default="lang_sfapi_agent",
        help="Name of the SFAPI flow to use",
    )
    parser.add_argument(
        "--session-id",
        default="sfapi_stream_demo",
        help="Session identifier to preserve history between runs",
    )
    parser.add_argument(
        "--user-id",
        default="sfapi_stream_user",
        help="User identifier to attribute the request",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Stream only chunk content to stdout (no chunk labels).",
    )
    parser.add_argument(
        "--show-metadata",
        action="store_true",
        help="Print chunk metadata for debugging the streaming contract.",
    )
    args = parser.parse_args()

    required_env_vars = ["CBORG_API_KEY", "CBORG_API_URL", "NERSC_CLIENT_ID", "NERSC_PRIVATE_KEY_PATH"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠️  Warning: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("The demo may fail without these variables.\n")

    print("🔧 Initializing ATHOS configuration...")
    cfg = build_config(args.config)

    if args.flow not in cfg.flows:
        raise SystemExit(f"Flow '{args.flow}' not found in config; available: {', '.join(cfg.flows)}")

    runner = FlowRunner(cfg)
    try:
        await stream_flow(
            runner=runner,
            flow_name=args.flow,
            message=args.message,
            session_id=args.session_id,
            user_id=args.user_id,
            show_metadata=args.show_metadata,
            stream_stdout=args.raw,
        )
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
