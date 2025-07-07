# ATHOS - Agentic AI Toolkit for HPC Operations
# Built on top of Hugging Face SmolAgents

import asyncio
import logging
from dotenv import load_dotenv

from athos.runtime import build_config, build_flow

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


# CLI interface (basic example)
async def main():
    """Main CLI interface for ATHOS"""
    import argparse

    parser = argparse.ArgumentParser(
        description="ATHOS - Agentic AI Toolkit for HPC Operations"
    )
    parser.add_argument(
        "--config", required=True, help="Path to configuration YAML file"
    )
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
        cfg = build_config(args.config)
        if args.log_level:
            logging.getLogger().setLevel(getattr(logging, args.log_level))
        flow = build_flow(args.flow, cfg)
        result = await flow.execute(args.input)
        print(f"Result: {result}")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise e
    finally:
        try:
            flow.close()
        except Exception as e:  # pragma: no cover - cleanup failures shouldn't crash
            logger.warning("Error during flow cleanup: %s", e)

    return 0


if __name__ == "__main__":
    asyncio.run(main())
