# Development Plan: Consolidate Athos Example Scripts

## 1. Objective

Consolidate four redundant example scripts into two improved, more versatile examples. This will reduce code duplication and create higher-quality examples that better demonstrate the features of the Athos framework.

## 2. Rationale

The current example scripts have overlapping functionality:
- `src/athos/examples/chatbot.py` and `src/athos/examples/langgraph_chatbot.py` both demonstrate chatbot flows.
- `src/athos/examples/web_agent.py` and `src/athos/examples/langgraph_web_agent.py` both demonstrate web agent flows.

This plan merges them into two generic scripts that can run the different flow implementations (e.g., `smolagents` vs. `langgraph`) based on command-line arguments. The new scripts will also showcase different runtime features like `FlowRunner`.

## 3. Implementation Steps

### Step 1: Create a Unified Chatbot Example

Create a new file named `src/athos/examples/chatbot_example.py` with the following content. This script merges the logic from `chatbot.py` and `langgraph_chatbot.py`.

```python
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
```

### Step 2: Create a Unified Web Agent Example

Create a new file named `src/athos/examples/web_agent_example.py` with the following content. This script is based on `langgraph_web_agent.py` to demonstrate the `FlowRunner` and is generalized to run different agent flows.

```python
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
        default="web_agent",
        help=(
            "Name of the agent flow to run. "
            "Try 'web_agent' or 'langchain_web_agent'."
        ),
    )
    args = parser.parse_args()

    await run_demo(config_path=args.config, flow_name=args.flow)


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Remove Redundant Example Scripts

Delete the following four files:
1.  `src/athos/examples/chatbot.py`
2.  `src/athos/examples/langgraph_chatbot.py`
3.  `src/athos/examples/web_agent.py`
4.  `src/athos/examples/langgraph_web_agent.py`

## 4. Verification

After implementing the changes, verify that the new scripts work correctly by running them from the command line with different flow names.

**Chatbot Example:**
```bash
# Run the smol-agent based chatbot
python src/athos/examples/chatbot_example.py --flow hpc_chatbot

# Run the langgraph-based chatbot
python src/athos/examples/chatbot_example.py --flow langgraph_chatbot_demo
```

**Web Agent Example:**
*Note: This example requires API keys (e.g., for Tavily) to be set in a `.env` file in the project root.*
```bash
# Run the smol-agent based web agent
python src/athos/examples/web_agent_example.py --flow web_agent

# Run the langgraph-based web agent
python src/athos/examples/web_agent_example.py --flow langchain_web_agent
```
