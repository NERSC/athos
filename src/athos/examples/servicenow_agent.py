"""
ATHOS ServiceNow Agent example - Demonstrates ServiceNow operations using the ATHOS framework.

This script shows how to leverage the ServiceNow MCP tools through ATHOS to
perform common ServiceNow tasks.

Features demonstrated:
1. Incident creation
2. Incident listing
3. Incident summary
4. Ticket triage (assignment)
5. Adding work notes
6. Ticket resolution

Requirements:
- ATHOS framework configured with `servicenow_mcp` server
- Environment variables: SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME,
  SERVICENOW_PASSWORD

The tasks to demonstrate can be selected via the ``--tasks`` argument. For
actions on an existing ticket (summary, triage, note, resolve) provide the
incident number with ``--incident``.
"""

import asyncio
import argparse
import os
import pprint
from dotenv import load_dotenv

from athos.runtime import build_config, build_flow

# Load environment variables from .env file
load_dotenv()


async def demonstrate_incident_summary(flow, incident: str) -> bool:
    """Summarize an existing incident."""
    print("\n🎯 Demonstrating Incident Summary...")
    print("=" * 60)

    task = f"""
    Summarize ServiceNow incident {incident}. Include the short description,
    current state, assignment group, assignee, and the most recent work note.
    """

    print("📝 Task: Summarize incident")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error summarizing incident: {e}")
        return False

    return True


async def demonstrate_triage_incident(flow, incident: str) -> bool:
    """Assign the incident to DAS group and Steven Farrell."""
    print("\n🎯 Demonstrating Incident Triage...")
    print("=" * 60)

    task = f"""
    Assign incident {incident} to the DAS assignment group and set the assignee
    to Steven Farrell. Provide a short confirmation of the new assignee and
    group.
    """

    print("📝 Task: Triage incident")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error triaging incident: {e}")
        return False

    return True


async def demonstrate_add_work_note(flow, incident: str) -> bool:
    """Add a work note to the incident."""
    print("\n🎯 Demonstrating Adding Work Note...")
    print("=" * 60)

    task = f"""
    Add a work note to incident {incident} saying: "This issue has been received
    and we are investigating." Return confirmation once the note is added.
    """

    print("📝 Task: Add work note")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error adding work note: {e}")
        return False

    return True


async def demonstrate_resolve_incident(flow, incident: str) -> bool:
    """Resolve the incident with close notes."""
    print("\n🎯 Demonstrating Incident Resolution...")
    print("=" * 60)

    task = f"""
    Resolve incident {incident} with the close notes "Resolved by ATHOS demo".
    Provide a confirmation of the resolution status.
    """

    print("📝 Task: Resolve incident")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error resolving incident: {e}")
        return False

    return True


async def demonstrate_incident_creation(flow) -> bool:
    """Create a test incident in ServiceNow."""
    print("\n🎯 Demonstrating Incident Creation...")
    print("=" * 60)

    task = """
    Please create a new incident in ServiceNow with the short description
    "ATHOS demo incident" and description "This incident was created by the
    ATHOS ServiceNow example." Return the incident number and sys_id.
    """

    print("📝 Task: Create incident")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error creating incident: {e}")
        return False

    return True


async def demonstrate_incident_listing(flow) -> bool:
    """List recent incidents."""
    print("\n🎯 Demonstrating Incident Listing...")
    print("=" * 60)

    task = """
    List the five most recent incidents in ServiceNow and display their
    numbers, short descriptions, and states.
    """

    print("📝 Task: List incidents")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await flow.execute(task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error listing incidents: {e}")
        return False

    return True




async def main() -> None:
    """Run the ServiceNow demonstration."""
    print("🚀 ATHOS ServiceNow Demo")
    print("Using ATHOS framework with ServiceNow MCP tools")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="ATHOS ServiceNow demo")
    parser.add_argument("--config", default="config/config.yaml",
                        help="Path to configuration YAML file")
    parser.add_argument("--flow", default="servicenow_agent",
                        help="Name of the ServiceNow flow to use")
    parser.add_argument(
        "--tasks",
        default="list",
        help=(
            "Comma-separated list of tasks to run. Available tasks: "
            "create,list,summary,triage,note,resolve"
        ),
    )
    parser.add_argument(
        "--incident",
        help="Incident number for summary, triage, note, or resolve tasks",
    )

    args = parser.parse_args()

    required_env_vars = [
        "SERVICENOW_INSTANCE_URL",
        "SERVICENOW_USERNAME",
        "SERVICENOW_PASSWORD",
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠️  Warning: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("The demo may fail without these variables.\n")

    # Initialize ATHOS manager
    print("🔧 Initializing ATHOS...")
    cfg = build_config(args.config)

    # Print available flows for reference
    print("\n📋 Available flows:")
    for flow_name in cfg.flows:
        s = f"  - {flow_name}"
        if flow_name == args.flow:
            s += "    ⭐ (selected for demo)"
        print(s)

    print(f"\n🎯 Using flow: {args.flow}")
    pprint.pprint(cfg.flows[args.flow], indent=6)

    # Build the flow
    flow = build_flow(args.flow, cfg)

    selected_tasks = [t.strip() for t in args.tasks.split(',') if t.strip()]

    incident_required = {"summary", "triage", "note", "resolve"}
    if incident_required.intersection(selected_tasks) and not args.incident:
        print("❌ Error: --incident must be provided for one or more selected tasks")
        return

    task_funcs = {
        "create": lambda: demonstrate_incident_creation(flow),
        "list": lambda: demonstrate_incident_listing(flow),
        "summary": lambda: demonstrate_incident_summary(flow, args.incident),
        "triage": lambda: demonstrate_triage_incident(flow, args.incident),
        "note": lambda: demonstrate_add_work_note(flow, args.incident),
        "resolve": lambda: demonstrate_resolve_incident(flow, args.incident),
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


if __name__ == "__main__":
    print("Starting ATHOS ServiceNow demo...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
