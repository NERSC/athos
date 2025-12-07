"""
ATHOS Filesystem Agent example - Demonstration of filesystem operations using ATHOS framework

This script demonstrates how to use the ATHOS framework with MCP filesystem tools
to perform file and directory operations. It replicates the functionality of the
standalone mcp_filesystem_agent.py but uses the ATHOS framework architecture.

Features demonstrated:
1. Basic file operations (create, write, read)
2. Directory listing
3. Advanced operations (directory creation, multiple files)
4. Summary generation

Requirements:
- ATHOS framework configured with filesystem_mcp server
- npm install -g @modelcontextprotocol/server-filesystem
"""

import asyncio
import argparse
import os
import pprint
from pathlib import Path
from dotenv import load_dotenv

from athos import build_config, build_flow
from athos.models import ExecutionMode, FlowInput, FlowSession

# Load environment variables from .env file
load_dotenv()


async def demonstrate_basic_filesystem_tasks(flow, session: FlowSession):
    """Demonstrate basic filesystem operations"""
    print("\n🎯 Demonstrating Basic Filesystem Tasks...")
    print("=" * 60)
    
    # Task 1: Create a test file and write content
    task1 = """
    Please help me with the following file management task:
    1. Create a new text file called 'athos_test.txt' in the current directory
    2. Write some sample content to it: "Hello from ATHOS with MCP Filesystem tools! This is a test file created by an AI agent using the ATHOS framework."
    3. Read the file back to confirm it was created correctly
    4. List the files in the current directory to show the file exists
    
    Please use the available filesystem tools to accomplish this task step by step.
    """
    
    print("📝 Task 1: Basic file creation and verification")
    print("Task description:", task1.strip())
    print("\n🏃 Executing task...")
    
    try:
        flow_input = FlowInput(
            message=task1.strip(),
            session=session,
            mode=ExecutionMode.SYNC,
            metadata={"task": "basic_file_operations"},
        )
        result1 = await flow.execute(flow_input)
        session.add_user_message(task1.strip())
        session.add_assistant_message(result1.content)
        print("\n✅ Task 1 completed!")
        print("📄 Agent response:")
        print(result1.content)
        if result1.metadata:
            print("📎 Metadata:")
            pprint.pprint(result1.metadata)
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error in Task 1: {e}")
        return False
    
    return True


async def demonstrate_advanced_filesystem_tasks(flow, session: FlowSession):
    """Demonstrate advanced filesystem operations"""
    print("\n🎯 Demonstrating Advanced Filesystem Tasks...")
    print("=" * 60)
    
    # Task 2: Advanced directory and file operations
    task2 = """
    Please perform the following advanced file management operations:
    1. Create a directory called 'athos_demo' if it doesn't exist
    2. Create three text files in that directory:
       - 'file1.txt' with content "First file created by ATHOS"
       - 'file2.txt' with content "Second file created by ATHOS"  
       - 'file3.txt' with content "Third file created by ATHOS"
    3. List all files in the 'athos_demo' directory
    4. Read the contents of all three files to verify they were created correctly
    5. Create a summary file called 'summary.txt' in the athos_demo directory that lists what files were created and their contents
    
    Please execute these operations step by step and provide status updates.
    """
    
    print("📝 Task 2: Advanced directory and file operations")
    print("Task description:", task2.strip())
    print("\n🏃 Executing advanced task...")
    
    try:
        flow_input = FlowInput(
            message=task2.strip(),
            session=session,
            mode=ExecutionMode.SYNC,
            metadata={"task": "advanced_file_operations"},
        )
        result2 = await flow.execute(flow_input)
        session.add_user_message(task2.strip())
        session.add_assistant_message(result2.content)
        print("\n✅ Task 2 completed!")
        print("📄 Agent response:")
        print(result2.content)
        if result2.metadata:
            print("📎 Metadata:")
            pprint.pprint(result2.metadata)
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error in Task 2: {e}")
        return False
    
    return True


async def demonstrate_file_exploration_task(flow, session: FlowSession):
    """Demonstrate file exploration and analysis"""
    print("\n🎯 Demonstrating File Exploration Task...")
    print("=" * 60)
    
    # Task 3: Explore and analyze the created files
    task3 = """
    Please explore the filesystem and provide an analysis:
    1. List all files and directories in the current working directory
    2. If the 'athos_demo' directory exists, explore its contents
    3. Count the total number of files created during our demo
    4. Calculate the total size of all text files (if possible)
    5. Create a final report file called 'demo_report.txt' that summarizes:
       - What files and directories were created
       - The content of each file
       - Any observations about the filesystem operations performed
    
    Please provide a comprehensive analysis of the filesystem state.
    """
    
    print("📝 Task 3: File exploration and analysis")
    print("Task description:", task3.strip())
    print("\n🏃 Executing exploration task...")
    
    try:
        flow_input = FlowInput(
            message=task3.strip(),
            session=session,
            mode=ExecutionMode.SYNC,
            metadata={"task": "file_exploration"},
        )
        result3 = await flow.execute(flow_input)
        session.add_user_message(task3.strip())
        session.add_assistant_message(result3.content)
        print("\n✅ Task 3 completed!")
        print("📄 Agent response:")
        print(result3.content)
        if result3.metadata:
            print("📎 Metadata:")
            pprint.pprint(result3.metadata)
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error in Task 3: {e}")
        return False
    
    return True


def setup_demo_workspace(demo_dir: str | Path | None = None):
    """Set up a clean workspace for the demo"""
    print("🔧 Setting up demo workspace...")

    if demo_dir is None:
        demo_dir = os.getenv("ATHOS_WORKSPACE", "./athos_filesystem_demo")

    # Create a working directory for the demo
    work_dir = Path(demo_dir)
    work_dir.mkdir(exist_ok=True)
    
    # Change to the working directory
    original_dir = os.getcwd()
    os.chdir(work_dir)
    
    print(f"📁 Demo workspace: {work_dir.absolute()}")
    print(f"📂 Current directory: {os.getcwd()}")
    
    return original_dir, work_dir


def cleanup_demo_workspace(original_dir):
    """Clean up and return to original directory"""
    print("\n🧹 Cleaning up demo workspace...")
    os.chdir(original_dir)
    print(f"📂 Returned to: {os.getcwd()}")


async def main():
    """Main demonstration function"""
    print("🚀 ATHOS Filesystem Demo")
    print("Using ATHOS framework with MCP filesystem tools")
    print("=" * 60)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ATHOS filesystem demo")
    parser.add_argument("--config", default="config/config.yaml",
                        help="Path to configuration YAML file")
    parser.add_argument("--flow", default="smol_filesystem_agent",
                        help="Name of the filesystem flow to use")
    parser.add_argument(
        "--demo-dir",
        default=os.getenv("ATHOS_WORKSPACE", "./athos_filesystem_demo"),
        help="Directory to use for demo files",
    )
    args = parser.parse_args()

    # Capture initial working directory so relative paths resolve correctly
    initial_cwd = Path.cwd()

    config_path = Path(args.config).expanduser()
    if not config_path.is_absolute():
        config_path = (initial_cwd / config_path).resolve()

    demo_dir = Path(args.demo_dir).expanduser()
    if not demo_dir.is_absolute():
        demo_dir = (initial_cwd / demo_dir).resolve()
    
    # Check for required environment variables
    required_env_vars = ["CBORG_API_KEY", "CBORG_API_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Warning: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("Please set these variables for the demo to work properly.")
        print("Continuing with demo (may fail if API access is required)...\n")
    
    # Set up workspace
    original_dir, work_dir = setup_demo_workspace(demo_dir)
    
    try:
        # Initialize ATHOS manager
        print("🔧 Initializing ATHOS...")
        cfg = build_config(str(config_path))
        
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
        flow = await build_flow(args.flow, cfg)

        session = FlowSession(
            session_id="filesystem_demo",
            user_id="demo_user",
            workspace=work_dir,
            interface="filesystem_demo",
        )

        # Execute demonstration tasks
        success_count = 0
        
        # Task 1: Basic filesystem operations
        if await demonstrate_basic_filesystem_tasks(flow, session):
            success_count += 1

        # Task 2: Advanced filesystem operations
        if await demonstrate_advanced_filesystem_tasks(flow, session):
            success_count += 1

        # Task 3: File exploration and analysis
        if await demonstrate_file_exploration_task(flow, session):
            success_count += 1
        
        # Summary
        print("\n🎉 Demo Summary")
        print("=" * 60)
        print(f"✅ Completed tasks: {success_count}/3")
        print(f"📁 Demo workspace: {work_dir.absolute()}")
        print("📝 Files created during demo should be visible in the workspace")
        
        if success_count == 3:
            print("🎊 All tasks completed successfully!")
        else:
            print("⚠️  Some tasks encountered errors - check the output above")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always clean up
        cleanup_demo_workspace(original_dir)
        print("\n👋 ATHOS Filesystem Demo completed!")


if __name__ == "__main__":
    print("Starting ATHOS filesystem demo...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
