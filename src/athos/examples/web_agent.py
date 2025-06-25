"""
Standalone smolagents example
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

    flow = "web_agent"

    query = "What are some upcoming or ongoing training events at NERSC?"
    result = await mgr.execute_flow(flow, query)
    print(f"Query: {query}")
    print(f"Result: {result}")

    # query = "What is NERSC?"
    # result = await mgr.execute_flow(flow, query)
    # print(f"Query: {query}")
    # print(f"Result: {result}")

    # query = "Where is it?"
    # result = await mgr.execute_flow(flow, query)
    # print(f"Query: {query}")
    # print(f"Result: {result}")

    # query = "What HPC systems do they have?"
    # result = await mgr.execute_flow(flow, query)
    # print(f"Query: {query}")
    # print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())

# model_id = "openai/gpt-4o"

# model = OpenAIServerModel(
#     model_id=model_id,
#     api_base="https://api.cborg.lbl.gov",
#     api_key=os.environ.get("CBORG_API_KEY"),
# )

# websearch_tool = DuckDuckGoSearchTool()
# webvisit_tool = VisitWebpageTool()

# agent = ToolCallingAgent(
#     tools=[websearch_tool, webvisit_tool],
#     model=model,
# )

# agent.run("How do I run pytorch in a container at NERSC?")
