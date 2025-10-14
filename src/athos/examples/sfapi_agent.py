"""ATHOS SFAPI Agent example - Demonstrates NERSC SuperFacility API tools."""

import asyncio
import argparse
import os
import pprint
from dotenv import load_dotenv

from athos import build_config, build_flow

# Load environment variables from .env if present
load_dotenv()


async def demonstrate_systems_status(flow) -> bool:
    """List available NERSC systems and their status."""
    print("\n🎯 Demonstrating Available Systems...")
    print("=" * 60)

    task = """
    What systems are available at NERSC and what are their current statuses?
    """

    print("📝 Task: System status")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error getting system status: {e}")
        return False

    return True


async def demonstrate_outage_summary(flow) -> bool:
    """Summarize recent unscheduled major outages."""
    print("\n🎯 Demonstrating Outage Summary...")
    print("=" * 60)

    task = """
    Summarize the most recent unscheduled major Perlmutter outages at NERSC.
    Provide a short summary of each.
    """

    print("📝 Task: Outage summary")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error summarizing outages: {e}")
        return False

    return True


async def demonstrate_project_membership(flow) -> bool:
    """List NERSC projects for the authenticated user."""
    print("\n🎯 Demonstrating Project Membership...")
    print("=" * 60)

    task = """
    Summarize my projects and associated allocations on Perlmutter.
    """

    print("📝 Task: Project membership")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error getting project membership: {e}")
        return False

    return True


async def main() -> None:
    """Run the SFAPI demonstration."""
    print("🚀 ATHOS SFAPI Demo")
    print("Using ATHOS framework with NERSC SFAPI MCP tools")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="ATHOS SFAPI demo")
    parser.add_argument("--config", default="config/config.yaml",
                        help="Path to configuration YAML file")
    parser.add_argument("--flow", default="sfapi_agent",
                        help="Name of the SFAPI flow to use")
    parser.add_argument(
        "--tasks",
        default="systems,outages",
        help=(
            "Comma-separated list of tasks to run. Available tasks: "
            "systems,outages,projects"
        ),
    )
    args = parser.parse_args()

    required_env_vars = [
        "CBORG_API_KEY",
        "CBORG_API_URL",
        "NERSC_CLIENT_ID",
        "NERSC_PRIVATE_KEY_PATH",
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠️  Warning: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("The demo may fail without these variables.\n")

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

    flow = build_flow(args.flow, cfg)

    selected_tasks = [t.strip() for t in args.tasks.split(',') if t.strip()]

    task_funcs = {
        "systems": lambda: demonstrate_systems_status(flow),
        "outages": lambda: demonstrate_outage_summary(flow),
        "projects": lambda: demonstrate_project_membership(flow),
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


def run_demo():
    """Entry point for running the demo"""
    print("Starting ATHOS SFAPI demo...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")


if __name__ == "__main__":
    run_demo()
else:
    # When run as a module (python -m athos.examples.sfapi_agent)
    # Execute the demo directly
    run_demo()
