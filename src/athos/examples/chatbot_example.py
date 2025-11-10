"""Example script for running chatbot flows in Athos."""

from __future__ import annotations

import argparse
import asyncio
from typing import Iterable

from athos import build_config
from athos.runtime.runner import FlowRunner


async def run_demo(*, config_path: str, flow_name: str) -> None:
    """Run a few conversation turns against a selected chatbot flow."""

    cfg = build_config(config_path)
    runner = FlowRunner(cfg)

    print(f"Running chatbot flow '{flow_name}' using config {config_path}\n")

    # --- Define a generic conversation to test the chatbot ---
    turns: Iterable[str] = (
        "Hello! Who are you?",
        "What kinds of problems can you help me solve?",
        "Thanks for the help!",
    )
    session_id = f"{flow_name}-demo"
    user_id = "demo"

    try:
        # --- Run conversation ---
        for turn in turns:
            print(f"User: {turn}")

            result = await runner.execute(
                flow_name=flow_name,
                message=turn,
                session_id=session_id,
                user_id=user_id,
                interface="cli",
            )

            if not result.success or result.output is None:
                print(f"Assistant: Error - {result.error}\n")
                continue

            response_content = result.output.content
            print(f"Assistant: {response_content}\n")
    finally:
        await runner.cleanup()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an Athos chatbot flow from the command line."
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the Athos configuration file to load.",
    )
    parser.add_argument(
        "--flow",
        default="hpc_chatbot",
        help=(
            "Name of the chatbot flow to run. "
            "Try 'hpc_chatbot' or 'langgraph_chatbot_demo'."
        ),
    )
    args = parser.parse_args()

    await run_demo(config_path=args.config, flow_name=args.flow)


if __name__ == "__main__":
    asyncio.run(main())
