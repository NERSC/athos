"""ATHOS Docs RAG Agent example - Demonstrates querying NERSC documentation via the RAG MCP server."""

import os
import asyncio
import argparse
import pprint
import uuid
from dotenv import load_dotenv

from athos import build_config, build_flow
from athos.models.flow import FlowInput
from athos.models.session import FlowSession
from athos.models.enums import ExecutionMode

# Load environment variables from .env if present
load_dotenv()


async def demonstrate_pytorch_query(flow) -> bool:
    """Ask how to run PyTorch workloads at NERSC."""
    print("\n🎯 Demonstrating PyTorch query...")
    print("=" * 60)

    task = """
    How can I run PyTorch workloads at NERSC? Mention supported systems and any
    required modules or instructions.
    """

    print("📝 Task: PyTorch query")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    session_id = str(uuid.uuid4())
    user_id = "docs_rag_demo_user"
    flow_session = FlowSession(session_id=session_id, user_id=user_id)
    flow_input = FlowInput(message=task, session=flow_session, mode=ExecutionMode.SYNC)

    try:
        result = await flow.execute(flow_input)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result.content)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error executing PyTorch query: {e}")
        return False

    return True


async def demonstrate_data_transfer_query(flow) -> bool:
    """Ask how to transfer data to NERSC."""
    print("\n🎯 Demonstrating Data Transfer query...")
    print("=" * 60)

    task = """
    How do I transfer data to NERSC? Provide steps and tools that should be used
    by users.
    """

    print("📝 Task: Data Transfer query")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    session_id = str(uuid.uuid4())
    user_id = "docs_rag_demo_user"
    flow_session = FlowSession(session_id=session_id, user_id=user_id)
    flow_input = FlowInput(message=task, session=flow_session, mode=ExecutionMode.SYNC)

    try:
        result = await flow.execute(flow_input)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result.content)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error executing Data Transfer query: {e}")
        return False

    return True


async def main() -> None:
    """Run the Docs RAG demonstration."""
    print("🚀 ATHOS Docs RAG Demo")
    print("Using ATHOS with the documentation RAG MCP tools")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="ATHOS Docs RAG demo")
    parser.add_argument("--config", default="config/config.yaml",
                        help="Path to configuration YAML file")
    parser.add_argument("--flow", default="smol_docs_agent",
                        help="Name of the Docs RAG flow to use")
    parser.add_argument(
        "--tasks",
        default="pytorch",
        help=(
            "Comma-separated list of tasks to run. Available tasks: "
            "pytorch,transfer"
        ),
    )
    args = parser.parse_args()

    print("🔧 Initializing ATHOS...")
    cfg = build_config(args.config)

    print("\n📋 Available flows:")
    for flow_name in cfg.flows:
        s = f"  - {flow_name}"
        if flow_name == args.flow:
            s += "    ⭐ (selected for demo)"
        print(s)

    print(f"\n🎯 Using flow: {args.flow}")
    pprint.pprint(cfg.flows[args.flow], indent=6)

    flow = await build_flow(args.flow, cfg)

    selected_tasks = [t.strip() for t in args.tasks.split(',') if t.strip()]

    task_funcs = {
        "pytorch": lambda: demonstrate_pytorch_query(flow),
        "transfer": lambda: demonstrate_data_transfer_query(flow),
    }

    success_count = 0
    for name in selected_tasks:
        func = task_funcs.get(name)
        if not func:
            print(f"⚠️  Unknown task: {name}")
            continue
        if await func():
            success_count += 1

    total = len(selected_tasks)

    print("\n🎉 Demo Summary")
    print("=" * 60)
    print(f"✅ Completed tasks: {success_count}/{total}")
    if success_count == total:
        print("🎊 All tasks completed successfully!")
    else:
        print("⚠️  Some tasks encountered errors - check the output above")


def run_demo() -> None:
    """Entry point for running the demo."""
    print("Starting ATHOS Docs RAG demo...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")


if __name__ == "__main__":
    run_demo()
else:
    # When run as a module (python -m athos.examples.docs_rag_agent)
    # Execute the demo directly
    run_demo()
