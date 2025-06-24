# ATHOS - Agentic AI Toolkit for HPC Operations
# Built on top of Hugging Face SmolAgents
#
# TODO:
# - move configuration dataclasses to pydantic objects, automate env var handling
# - only load specified config(s), maybe with lazy initialization?
# - split configuration across multiple yaml files
# - enable gradio UI integration for smolagents

import asyncio
import logging

from athos.core.manager import create_athos_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# CLI interface (basic example)
async def main():
    """Main CLI interface for ATHOS"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ATHOS - Agentic AI Toolkit for HPC Operations")
    parser.add_argument("--config", required=True, help="Path to configuration YAML file")
    parser.add_argument("--flow", required=True, help="Execution flow name")
    parser.add_argument("--input", required=True, help="Input for the execution flow")
    
    args = parser.parse_args()

    try:
        mgr = create_athos_manager(args.config)
        result = await mgr.execute_flow(args.flow, args.input)
        print(f"Result: {result}")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise e
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())
