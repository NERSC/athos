"""
Complete example demonstrating HuggingFace SmolAgents with OpenAI MCP Filesystem Tool

This script shows how to:
1. Initialize the MCP filesystem client with stdio using SmolAgents' MCPClient
2. Explore and summarize available tools
3. Create a ToolCallingAgent with filesystem capabilities
4. Execute a simple file management task

Requirements:
pip install smolagents mcp openai
npm install -g @modelcontextprotocol/server-filesystem
"""

import asyncio
import os
from typing import List

from mcp import StdioServerParameters

try:
    from smolagents import ToolCallingAgent, MCPClient, OpenAIServerModel
except ImportError:
    print("Please install smolagents: pip install smolagents")
    exit(1)


async def initialize_mcp_client():
    """Initialize MCP filesystem client using SmolAgents' MCPClient"""
    print("🔧 Initializing MCP Filesystem Client...")
    
    # Create a working directory for the demo
    work_dir = os.path.abspath("./mcp_demo_workspace")
    os.makedirs(work_dir, exist_ok=True)
    print(f"📁 Using working directory: {work_dir}")
    
    # Clean up any existing processes first
    print("🧹 Cleaning up any existing MCP processes...")
    import subprocess
    try:
        subprocess.run(["pkill", "-f", "server-filesystem"], 
                      capture_output=True, timeout=5)
        await asyncio.sleep(1)  # Give time for cleanup
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Ignore if pkill fails or doesn't exist
    
    try:
        # Create MCPClient with filesystem server using StdioServerParameters
        mcp_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", work_dir],
            env=dict(os.environ)
        )
        
        print("🔌 Creating fresh MCPClient instance...")
        mcp_client = MCPClient(mcp_params)
        
        # print("🤝 Connecting to MCP server...")
        # Initialize the client with timeout
        # await asyncio.wait_for(mcp_client.connect(), timeout=15.0)
        
        print("✅ MCP Filesystem client initialized successfully!")
        print(f"🏠 Server is operating in: {work_dir}")
        return mcp_client
        
    except asyncio.TimeoutError:
        print("❌ Timeout while connecting to MCP server")
        return None
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if it's the threading error specifically
        if "threads can only be started once" in str(e):
            print("\n🔄 Threading error detected. This usually means:")
            print("   1. A previous script run didn't clean up properly")
            print("   2. There are still MCP processes running")
            print("\n💡 Try these solutions:")
            print("   1. Restart your Python interpreter/terminal")
            print("   2. Run: pkill -f 'server-filesystem'")
            print("   3. Wait a few seconds and try again")
            
        print("\nGeneral troubleshooting:")
        print("1. Make sure you have the MCP filesystem server installed:")
        print("   npm install -g @modelcontextprotocol/server-filesystem")
        print("2. Verify Node.js is installed and npx is available")
        print("3. Try running the server manually:")
        print(f"   npx -y @modelcontextprotocol/server-filesystem {work_dir}")
        return None


async def explore_available_tools(mcp_client: MCPClient):
    """Explore and summarize available MCP tools"""
    print("\n📋 Exploring Available Tools...")
    
    try:
        # Get tools from the MCP client
        tools = await asyncio.to_thread(mcp_client.get_tools)
        
        if not tools:
            print("No tools available from MCP server")
            return []
        
        print(f"Found {len(tools)} tools:")
        
        # Display information about each tool
        for tool in tools:
            print(f"\n🔨 Tool: {tool.name}")
            print(f"   Description: {tool.description}")
            
            # Show parameters if available
            if hasattr(tool, 'parameters') and tool.parameters:
                print("   Parameters:")
                for param_name, param_info in tool.parameters.items():
                    param_type = param_info.get('type', 'unknown')
                    param_desc = param_info.get('description', 'No description')
                    required = param_info.get('required', False)
                    req_str = " (required)" if required else " (optional)"
                    print(f"     - {param_name} ({param_type}){req_str}: {param_desc}")
            
            # Show input schema if available
            elif hasattr(tool, 'input_schema') and tool.input_schema:
                schema = tool.input_schema
                if 'properties' in schema:
                    print("   Parameters:")
                    for param, details in schema['properties'].items():
                        required = param in schema.get('required', [])
                        req_str = " (required)" if required else " (optional)"
                        param_type = details.get('type', 'unknown')
                        param_desc = details.get('description', 'No description')
                        print(f"     - {param} ({param_type}){req_str}: {param_desc}")
        
        return tools
        
    except Exception as e:
        print(f"❌ Error exploring tools: {e}")
        return []


async def create_agent_with_filesystem_tools(tools: List):
    """Create a ToolCallingAgent with filesystem tools"""
    print("\n🤖 Creating ToolCallingAgent...")
    
    if not tools:
        print("❌ No tools available to create agent")
        return None
    
    try:
        model = OpenAIServerModel(
            model_id="openai/gpt-4o-mini",
            api_base=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        # Create the agent with filesystem tools
        agent = ToolCallingAgent(
            tools=tools,
            model=model,  # Use OpenAI model
            max_steps=5
        )
        
        print("✅ ToolCallingAgent created successfully!")
        print(f"   Agent has access to {len(tools)} filesystem tools")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        print("Make sure you have your OpenAI API key set in OPENAI_API_KEY environment variable")
        return None


async def demonstrate_agent_task(agent: ToolCallingAgent):
    """Demonstrate the agent performing a simple filesystem task"""
    print("\n🎯 Demonstrating Agent Task...")
    
    if not agent:
        print("❌ No agent available for demonstration")
        return
    
    # Simple task: create a test file and read it back
    task = """
    Please help me with the following file management task:
    1. Create a new text file called 'smolagents_test.txt' in the current directory
    2. Write some sample content to it: "Hello from SmolAgents with MCP Filesystem tools! This is a test file created by an AI agent."
    3. Read the file back to confirm it was created correctly
    4. List the files in the current directory to show the file exists
    
    Please use the available filesystem tools to accomplish this task step by step.
    """
    
    try:
        print("📝 Task assigned to agent:")
        print(task)
        print("\n🏃 Agent executing task...")
        
        # Run the agent
        result = await asyncio.to_thread(agent.run, task)
        
        print("\n✅ Agent task completed!")
        print("📄 Agent response:")
        print(result)
        
    except Exception as e:
        print(f"❌ Error during agent task execution: {e}")


async def demonstrate_advanced_task(agent: ToolCallingAgent):
    """Demonstrate a more advanced filesystem task"""
    print("\n🎯 Demonstrating Advanced Task...")
    
    if not agent:
        print("❌ No agent available for demonstration")
        return
    
    # More complex task involving multiple operations
    task = """
    Please perform the following advanced file management operations:
    1. Create a directory called 'smolagents_demo' if it doesn't exist
    2. Create three text files in that directory:
       - 'file1.txt' with content "First file"
       - 'file2.txt' with content "Second file"  
       - 'file3.txt' with content "Third file"
    3. List all files in the 'smolagents_demo' directory
    4. Read the contents of all three files to verify they were created correctly
    5. Create a summary file called 'summary.txt' that lists what files were created
    
    Please execute these operations step by step and provide status updates.
    """
    
    try:
        print("📝 Advanced task assigned to agent:")
        print(task)
        print("\n🏃 Agent executing advanced task...")
        
        # Run the agent
        result = await asyncio.to_thread(agent.run, task)
        
        print("\n✅ Advanced agent task completed!")
        print("📄 Agent response:")
        print(result)
        
    except Exception as e:
        print(f"❌ Error during advanced agent task execution: {e}")


async def cleanup_mcp_client(mcp_client: MCPClient):
    """Clean up the MCP client"""
    if mcp_client:
        try:
            # Properly close the client and its resources
            await asyncio.to_thread(mcp_client.disconnect)
            print("\n🧹 MCP client closed successfully")
        except Exception as e:
            print(f"⚠️  Warning: Error closing MCP client: {e}")


async def main():
    """Main demonstration function"""
    print("🚀 HuggingFace SmolAgents + OpenAI MCP Filesystem Demo")
    print("=" * 60)
    
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        print("Continuing with demo (agent creation may fail)...\n")
    
    mcp_client = None
    
    try:
        # Step 1: Initialize MCP filesystem client
        mcp_client = await initialize_mcp_client()
        if not mcp_client:
            return
        
        # Step 2: Explore available tools
        tools = await explore_available_tools(mcp_client)
        if not tools:
            await cleanup_mcp_client(mcp_client)
            return
        
        # Step 3: Create agent with tools
        agent = await create_agent_with_filesystem_tools(tools)
        if not agent:
            await cleanup_mcp_client(mcp_client)
            return
        
        # Step 4: Demonstrate basic agent task
        await demonstrate_agent_task(agent)
        
        # Step 5: Demonstrate advanced agent task
        print("\n" + "=" * 60)
        await demonstrate_advanced_task(agent)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup - ensure this always happens
        if mcp_client:
            await cleanup_mcp_client(mcp_client)
        print("\n👋 Demo completed!")


if __name__ == "__main__":
    # Clean up any existing processes before starting
    import subprocess
    try:
        subprocess.run(["pkill", "-f", "server-filesystem"], 
                      capture_output=True, timeout=5)
    except:
        pass
    
    # Run the demonstration
    print("Starting async demo...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Script failed: {e}")
        # Final cleanup attempt
        try:
            subprocess.run(["pkill", "-f", "server-filesystem"], 
                          capture_output=True, timeout=5)
        except:
            pass