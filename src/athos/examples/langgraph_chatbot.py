"""Example script showing how to run the LangGraph chatbot flow."""

from __future__ import annotations

import argparse
import asyncio
from typing import Iterable

from athos import build_config, build_flow


async def run_demo(*, config_path: str, flow_name: str) -> None:
    """Run a few conversation turns against the LangGraph chatbot flow."""

    cfg = build_config(config_path)
    chatbot_flow = build_flow(flow_name, cfg)

    print(f"Running LangGraph chatbot flow '{flow_name}' using config {config_path}\n")

    turns: Iterable[str] = (
        "Hello! Who are you?",
        "What kinds of problems can you help me solve?",
        "Thanks for the help!",
    )

    for turn in turns:
        response = await chatbot_flow.execute(turn)
        print(f"User: {turn}")
        print(f"Assistant: {response}\n")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the LangGraph chatbot flow example from the command line."
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the Athos configuration file to load.",
    )
    parser.add_argument(
        "--flow-name",
        default="langgraph_chatbot_demo",
        help="Name of the LangGraph chatbot flow defined in the configuration file.",
    )
    args = parser.parse_args()

    await run_demo(config_path=args.config, flow_name=args.flow_name)


if __name__ == "__main__":
    asyncio.run(main())
