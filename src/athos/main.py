# ATHOS - Agentic AI Toolkit for HPC Operations
# Built on top of Hugging Face SmolAgents

import asyncio
import logging

from athos.core.manager import create_athos_manager

logger = logging.getLogger(__name__)


# CLI interface (basic example)
async def main():
    """Main CLI interface for ATHOS"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ATHOS - Agentic AI Toolkit for HPC Operations")
    parser.add_argument("--config", required=True, help="Path to configuration YAML file")
    parser.add_argument("--flow", required=True, help="Execution flow name")
    parser.add_argument("--input", required=True, help="Input for the execution flow")
    parser.add_argument(
        "-v",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override logging level for this run",
    )
    
    args = parser.parse_args()

    try:
        mgr = create_athos_manager(args.config)
        if args.log_level:
            logging.getLogger().setLevel(getattr(logging, args.log_level))
        result = await mgr.execute_flow(args.flow, args.input)
        print(f"Result: {result}")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise e
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())
