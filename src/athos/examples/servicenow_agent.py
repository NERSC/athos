"""
ATHOS ServiceNow Agent example - Demonstrates ServiceNow operations using the ATHOS framework.

This script shows how to leverage the ServiceNow MCP tools through ATHOS to
perform common ServiceNow tasks.

Features demonstrated:
1. Incident creation
2. Incident listing
3. Knowledge base search
4. Incident summary
5. Ticket triage (assignment)
6. Adding work notes
7. Ticket resolution

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

from athos.core.manager import create_athos_manager


async def demonstrate_incident_summary(mgr, flow_name: str, incident: str) -> bool:
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
        result = await mgr.execute_flow(flow_name, task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error summarizing incident: {e}")
        return False

    return True


async def demonstrate_triage_incident(mgr, flow_name: str, incident: str) -> bool:
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
        result = await mgr.execute_flow(flow_name, task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error triaging incident: {e}")
        return False

    return True


async def demonstrate_add_work_note(mgr, flow_name: str, incident: str) -> bool:
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
        result = await mgr.execute_flow(flow_name, task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error adding work note: {e}")
        return False

    return True


async def demonstrate_resolve_incident(mgr, flow_name: str, incident: str) -> bool:
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
        result = await mgr.execute_flow(flow_name, task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error resolving incident: {e}")
        return False

    return True


async def demonstrate_incident_creation(mgr, flow_name: str) -> bool:
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
        result = await mgr.execute_flow(flow_name, task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error creating incident: {e}")
        return False

    return True


async def demonstrate_incident_listing(mgr, flow_name: str) -> bool:
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
        result = await mgr.execute_flow(flow_name, task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error listing incidents: {e}")
        return False

    return True


async def demonstrate_knowledge_search(mgr, flow_name: str) -> bool:
    """Search the knowledge base for a common article."""
    print("\n🎯 Demonstrating Knowledge Base Search...")
    print("=" * 60)

    task = """
    Search the ServiceNow knowledge base for articles about resetting a user
    password. Return the titles of up to three relevant articles.
    """

    print("📝 Task: Search knowledge base")
    print("Task description:", task.strip())
    print("\n🏃 Executing task...")

    try:
        result = await mgr.execute_flow(flow_name, task)
        print("\n✅ Task completed!")
        print("📄 Agent response:")
        print(result)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error searching knowledge base: {e}")
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
        default="create,list,search",
        help=(
            "Comma-separated list of tasks to run. Available tasks: "
            "create,list,search,summary,triage,note,resolve"
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

    mgr = create_athos_manager(args.config)

    print("\n📋 Available flows:")
    for flow in mgr.list_flows():
        print(f"  - {flow}")
        if flow == args.flow:
            print("    ⭐ (selected for demo)")
            #pprint.pprint(mgr.describe_flow(flow), indent=6)

    print(f"\n🎯 Using flow: {args.flow}")

    if args.flow not in mgr.list_flows():
        print(f"❌ Error: Flow '{args.flow}' not found in configuration")
        print("Available flows:", mgr.list_flows())
        return

    selected_tasks = [t.strip() for t in args.tasks.split(',') if t.strip()]

    incident_required = {"summary", "triage", "note", "resolve"}
    if incident_required.intersection(selected_tasks) and not args.incident:
        print("❌ Error: --incident must be provided for one or more selected tasks")
        return

    task_funcs = {
        "create": lambda: demonstrate_incident_creation(mgr, args.flow),
        "list": lambda: demonstrate_incident_listing(mgr, args.flow),
        "search": lambda: demonstrate_knowledge_search(mgr, args.flow),
        "summary": lambda: demonstrate_incident_summary(mgr, args.flow, args.incident),
        "triage": lambda: demonstrate_triage_incident(mgr, args.flow, args.incident),
        "note": lambda: demonstrate_add_work_note(mgr, args.flow, args.incident),
        "resolve": lambda: demonstrate_resolve_incident(mgr, args.flow, args.incident),
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
