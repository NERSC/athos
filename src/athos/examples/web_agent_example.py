"""Example demonstrating how to run ReAct agent flows with web search."""

from __future__ import annotations

import argparse
import asyncio
import pprint

from dotenv import load_dotenv

from athos import build_config
from athos.runtime.runner import FlowRunner


async def run_demo(*, config_path: str, flow_name: str) -> None:
    """Load the requested agent flow and execute a single sample query."""

    # Load environment variables from .env file for API keys (e.g., TAVILY_API_KEY)
    load_dotenv()

    cfg = build_config(config_path)
    runner = FlowRunner(cfg)

    print(f"Running agent flow '{flow_name}' using config {config_path}\n")

    print("Selected flow configuration:")
    pprint.pprint(cfg.flows[flow_name].model_dump())

    query = "What are some upcoming or ongoing training events at NERSC?"

    try:
        print(f"\nExecuting query: '{query}'...")
        result = await runner.execute(
            flow_name=flow_name,
            message=query,
            session_id=f"{flow_name}-demo",
            user_id="demo-user",
            interface="cli",
        )

        if not result.success or result.output is None:
            print("\nQuery execution failed:")
            print(f"Error: {result.error}")
            return

        print("\nQuery successful!")
        print(f"Result: {result.output.content}")

    finally:
        # Clean up any resources used by the runner (e.g., background services)
        await runner.cleanup()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an Athos agent flow with web search capabilities."
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the Athos configuration file to load.",
    )
    parser.add_argument(
        "--flow",
        default="smol_web_agent",
        help=(
            "Name of the agent flow to run. "
            "Try 'smol_web_agent' or 'lang_web_agent'."
        ),
    )
    args = parser.parse_args()

    await run_demo(config_path=args.config, flow_name=args.flow)


if __name__ == "__main__":
    asyncio.run(main())
