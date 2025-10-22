"""
Demonstration of simple chatbot capability in athos
"""

import asyncio
import argparse
import pprint

from athos import build_config, build_flow
from athos.models import ExecutionMode, FlowInput, FlowSession


async def main():
    parser = argparse.ArgumentParser(description="ATHOS chatbot example")
    parser.add_argument(
        "--config", default="config/config.yaml", help="Path to configuration YAML file"
    )
    args = parser.parse_args()

    cfg = build_config(args.config)
    chat_flow = await build_flow("hpc_chatbot", cfg)

    session = FlowSession(session_id="demo", user_id="demo")

    # Print some info about available flows
    print("Available flows:")
    for name in cfg.flows:
        print(f"- {name}")

    # Print info about hpc_chatbot flow
    pprint.pprint(cfg.flows["hpc_chatbot"])

    # Run some example questions in conversation
    for query in [
        "What is NERSC?",
        "Where is it?",
        "What HPC systems do they have?",
    ]:
        flow_input = FlowInput(
            message=query,
            session=session,
            mode=ExecutionMode.SYNC,
        )
        result = await chat_flow.execute(flow_input)
        session.add_message("user", query)
        session.add_message("assistant", result.content)
        print(f"Query: {query}")
        print(f"Result: {result.content}")


if __name__ == "__main__":
    asyncio.run(main())
