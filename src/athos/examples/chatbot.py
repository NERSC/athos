"""
Demonstration of simple chatbot capability in athos
"""

import asyncio
import argparse
import pprint
    
from athos.core.manager import create_athos_manager

async def main():
    parser = argparse.ArgumentParser(description="ATHOS chatbot example")
    parser.add_argument("--config", default="config/config.yaml",
                        help="Path to configuration YAML file")
    args = parser.parse_args()

    mgr = create_athos_manager(args.config)

    # Print some info about available flows
    for flow in mgr.list_flows():
        print(f"Flow: {flow}")
        pprint.pprint(mgr.get_flow_info(flow))
        print()

    # Run some example questions in conversation
    flow = "hpc_chatbot"

    query = "What is NERSC?"
    result = await mgr.execute_flow(flow, query)
    print(f"Query: {query}")
    print(f"Result: {result}")

    query = "Where is it?"
    result = await mgr.execute_flow(flow, query)
    print(f"Query: {query}")
    print(f"Result: {result}")

    query = "What HPC systems do they have?"
    result = await mgr.execute_flow(flow, query)
    print(f"Query: {query}")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
