# ATHOS - Agentic AI Toolkit for HPC Operations
# Built on top of Hugging Face SmolAgents

import asyncio
import logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from athos.runtime.builder import build_config, build_flow
from athos.runtime.runner import FlowRunner
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

    def _section_header(title: str) -> str:
        return f"{title}:"

    def _append_items(
        lines: List[str],
        items: Dict[str, Any],
        summary_getter,
    ) -> None:
        if not items:
            lines.append("  (none)")
            return

        for name, item in items.items():
            summary = summary_getter(item)
            description = getattr(item, "description", None)
            if summary:
                lines.append(f"  - {name}: {summary}")
            else:
                lines.append(f"  - {name}")
            if description:
                lines.append(f"      Description: {description}")

    lines: List[str] = ["Configuration Summary:"]

    def _model_summary(model: Any) -> str:
        return getattr(model, "model_id", "")

    def _tool_summary(tool: Any) -> str:
        module = getattr(tool, "module_path", "")
        callable_name = getattr(tool, "callable_name", "")
        if module and callable_name:
            return f"{module}.{callable_name}"
        return module or callable_name

    def _mcp_summary(mcp: Any) -> str:
        mcp_type = getattr(mcp, "mcp_type", "")
        return getattr(mcp_type, "value", mcp_type)

    def _flow_summary(flow: Any) -> str:
        flow_type = getattr(flow, "type", "")
        model_name = getattr(flow, "model", "")
        if flow_type and model_name:
            return f"{flow_type} (model={model_name})"
        return flow_type or model_name

    lines.append(_section_header("Models"))
    _append_items(lines, cfg.models, _model_summary)

    lines.append(_section_header("Tools"))
    _append_items(lines, cfg.tools, _tool_summary)

    lines.append(_section_header("MCP Servers"))
    _append_items(lines, cfg.mcp_servers, _mcp_summary)

    lines.append(_section_header("Flows"))
    _append_items(lines, cfg.flows, _flow_summary)

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
    runner: Optional[FlowRunner] = None
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
            flow = await build_flow(args.flow, cfg)
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
        runner = FlowRunner(cfg)
        result = await runner.execute(
            flow_name=args.flow,
            message=args.input,
            session_id="cli_session",
            user_id="cli_user",
            interface="cli",
            metadata={"cli": True},
        )

        if not result.success or result.output is None:
            print(f"Error: {result.error}")
            return 1

        print(result.output.content)

        for artifact in result.output.artifacts:
            print(f"\n[Artifact: {artifact.display_name or artifact.type}]")
            if artifact.path:
                print(f"  Path: {artifact.path}")
            elif artifact.data is not None:
                print(f"  Data: {artifact.data}")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise e
    finally:
        if runner is not None:
            try:
                await runner.cleanup()
            except Exception as e:  # pragma: no cover - cleanup failures shouldn't crash
                logger.warning("Error during runner cleanup: %s", e)
        if flow is not None:
            cleanup = getattr(flow, "cleanup", None)
            close = getattr(flow, "close", None)
            try:
                if callable(cleanup):
                    await cleanup()
                elif callable(close):
                    await close()
            except Exception as e:  # pragma: no cover - cleanup failures shouldn't crash
                logger.warning("Error during flow cleanup: %s", e)

    return 0


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    cli()
