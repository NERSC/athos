"""
Demonstration of simple chatbot capability in athos
"""

import asyncio
import argparse
import pprint

from athos import build_config, build_flow


async def main():
    parser = argparse.ArgumentParser(description="ATHOS chatbot example")
    parser.add_argument(
        "--config", default="config/config.yaml", help="Path to configuration YAML file"
    )
    args = parser.parse_args()

    cfg = build_config(args.config)
    chat_flow = build_flow("hpc_chatbot", cfg)

    # Print some info about available flows
    print("Available flows:")
    for name in cfg.flows:
        print(f"- {name}")

    # Print info about hpc_chatbot flow
    pprint.pprint(cfg.flows["hpc_chatbot"])

    # Run some example questions in conversation
    query = "What is NERSC?"
    result = await chat_flow.execute(query)
    print(f"Query: {query}")
    print(f"Result: {result}")

    query = "Where is it?"
    result = await chat_flow.execute(query)
    print(f"Query: {query}")
    print(f"Result: {result}")

    query = "What HPC systems do they have?"
    result = await chat_flow.execute(query)
    print(f"Query: {query}")
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
