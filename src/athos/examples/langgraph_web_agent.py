"""Example demonstrating the LangGraph ReAct agent with DuckDuckGo search."""

from __future__ import annotations

import argparse
import asyncio
import pprint

from dotenv import load_dotenv

from athos import build_config
from athos.runtime.runner import FlowRunner


async def run_demo(*, config_path: str, flow_name: str) -> None:
    """Load the requested flow and execute a single sample query."""

    # Load environment variables from .env file
    load_dotenv()

    cfg = build_config(config_path)

    print(
        f"Running LangGraph ReAct agent flow '{flow_name}' using config {config_path}\n"
    )

    print("Available flows in configuration:")
    for name in cfg.flows:
        print(f"- {name}")

    print("\nSelected flow configuration:")
    pprint.pprint(cfg.flows[flow_name].model_dump())

    query = "What are some upcoming or ongoing training events at NERSC?"
    runner = FlowRunner(cfg)

    try:
        result = await runner.execute(
            flow_name=flow_name,
            message=query,
            session_id="langgraph-web-agent-demo",
            user_id="demo-user",
            interface="cli",
        )

        if not result.success or result.output is None:
            print("\nQuery execution failed:")
            print(f"Error: {result.error}")
            return

        print(f"\nQuery: {query}")
        print(f"Result full: {result}")
        # print(f"Result: {result.output.content}")

        # Retrieve and print the conversation history
        session = await runner.session_store.get_or_create(
            session_id=result.session_id,
            user_id="demo-user",
        )
        history = session.get_history()
        print("\nConversation History:")
        pprint.pprint(history)
    finally:
        await runner.cleanup()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the LangGraph ReAct agent example which uses DuckDuckGo search."
        )
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the Athos configuration file to load.",
    )
    parser.add_argument(
        "--flow-name",
        default="langgraph_react_web_agent_demo",
        help="Name of the LangGraph ReAct flow defined in the configuration file.",
    )
    args = parser.parse_args()

    await run_demo(config_path=args.config, flow_name=args.flow_name)


if __name__ == "__main__":
    asyncio.run(main())
