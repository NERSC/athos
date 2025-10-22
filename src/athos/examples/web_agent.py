"""
Standalone smolagents example
"""

import asyncio
import argparse
import pprint
from pathlib import Path

from athos import build_config, build_flow
from athos.models.flow import FlowInput, FlowOutput
from athos.models.session import FlowSession
from athos.models.enums import ExecutionMode

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
    flow = await build_flow(flow_name, cfg)

    # Create a session for this demonstration
    session = FlowSession(
        session_id="web-agent-demo",
        user_id="demo-user",
        workspace=Path(cfg.workspace_path) / "demo-user" / "web-agent-demo",
        interface="cli"
    )

    # Run queries
    query = "What are some upcoming or ongoing training events at NERSC?"
    flow_input = FlowInput(
        message=query,
        session=session,
        mode=ExecutionMode.SYNC
    )
    result = await flow.execute(flow_input)
    print(f"Query: {query}")
    print(f"Result: {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
