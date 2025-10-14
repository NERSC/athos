"""
Standalone smolagents example
"""

import asyncio
import argparse
import pprint
    
from athos import build_config, build_flow

async def main():
    parser = argparse.ArgumentParser(description="ATHOS chatbot example")
    parser.add_argument("--config", default="config/config.yaml",
                        help="Path to configuration YAML file")
    args = parser.parse_args()

    # Load ATHOS configuration
    cfg = build_config(args.config)

    # Print some info about available flows
    print("Available flows:")
    for name in cfg.flows:
        print(f"- {name}")

    # Construct web_agent flow
    flow_name = "web_agent"
    print(f"Constructing flow {flow_name}")
    pprint.pprint(cfg.flows[flow_name])
    flow = build_flow(flow_name, cfg)

    # Run queries
    query = "What are some upcoming or ongoing training events at NERSC?"
    result = await flow.execute(query)
    print(f"Query: {query}")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
