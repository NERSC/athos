# ATHOS - Agentic AI Toolkit for HPC Operations
# Built on top of Hugging Face SmolAgents

import asyncio
import logging
from dotenv import load_dotenv

from athos.runtime import build_config, build_flow
from athos.utils import parse_overrides

# Only needed when launching a Gradio UI
try:  # pragma: no cover - optional dependency at runtime
    from smolagents import GradioUI
except Exception:  # pragma: no cover - smolagents not installed
    GradioUI = None

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def _format_config(cfg):
    """Create a human-friendly representation of configuration sections."""
    lines = ["Configuration Summary:"]

    lines.append("Models:")
    if cfg.models:
        for name, model in cfg.models.items():
            model_id = getattr(model, "model_id", "")
            lines.append(f"  - {name}: {model_id}")
    else:
        lines.append("  (none)")

    lines.append("Tools:")
    if cfg.tools:
        for name, tool in cfg.tools.items():
            module = getattr(tool, "module_path", "")
            callable_name = getattr(tool, "callable_name", "")
            lines.append(f"  - {name}: {module}.{callable_name}")
    else:
        lines.append("  (none)")

    lines.append("MCP Servers:")
    if cfg.mcp_servers:
        for name, mcp in cfg.mcp_servers.items():
            mcp_type = getattr(mcp, "mcp_type", "")
            mcp_type = getattr(mcp_type, "value", mcp_type)
            lines.append(f"  - {name}: {mcp_type}")
    else:
        lines.append("  (none)")

    lines.append("Flows:")
    if cfg.flows:
        for name, flow in cfg.flows.items():
            flow_type = getattr(flow, "type", "")
            lines.append(f"  - {name}: {flow_type}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


# CLI interface (basic example)
async def main():
    """Main CLI interface for ATHOS"""
    import argparse

    parser = argparse.ArgumentParser(
        description="ATHOS - Agentic AI Toolkit for HPC Operations"
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration YAML file"
    )
    parser.add_argument("--flow", help="Flow name")
    parser.add_argument("--input", help="Input for the flow")
    parser.add_argument(
        "--gradio",
        action="store_true",
        help="Launch a Gradio server for the specified flow",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the Gradio server on (default: 7860)",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Display loaded configuration and exit",
    )
    parser.add_argument(
        "-v",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override logging level for this run",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Override config values (e.g. models.gpt_4o.temperature=0.5)",
    )

    args = parser.parse_args()

    try:
        overrides = parse_overrides(args.set) if args.set else None
    except ValueError as exc:
        parser.error(str(exc))

    flow = None
    try:
        cfg = build_config(args.config, overrides)
        if args.log_level:
            logging.getLogger().setLevel(getattr(logging, args.log_level))
        if args.show_config:
            print(_format_config(cfg))
            return 0
        if args.gradio:
            if GradioUI is None:
                parser.error("smolagents with Gradio support is required to use --gradio")
            if not args.flow:
                parser.error("--flow is required when --gradio is used")
            flow = build_flow(args.flow, cfg)
            try:
                GradioUI(flow.agent).launch(
                    server_name="0.0.0.0", server_port=args.port, share=False
                )
            except KeyboardInterrupt:
                logger.info("Gradio server stopped by user")
            return 0
        if not args.flow or not args.input:
            parser.error(
                "--flow and --input are required unless --show-config or --gradio is used"
            )
        flow = build_flow(args.flow, cfg)
        result = await flow.execute(args.input)
        print(f"Result: {result}")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise e
    finally:
        if flow is not None:
            try:
                flow.close()
            except Exception as e:  # pragma: no cover - cleanup failures shouldn't crash
                logger.warning("Error during flow cleanup: %s", e)

    return 0


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    cli()
