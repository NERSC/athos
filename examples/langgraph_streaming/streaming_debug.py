"""Standalone LangChain streaming debugger.

Test different stream modes with controllable tools to understand
streaming behavior without ATHOS dependencies.

Usage:
    python examples/streaming_debug.py
    python examples/streaming_debug.py --stream-mode messages
    python examples/streaming_debug.py --stream-mode updates
    python examples/streaming_debug.py --stream-mode messages,updates
    python examples/streaming_debug.py --verbose
    python examples/streaming_debug.py --query "What's the weather in SF?"

Requirements:
    pip install langchain langchain-openai langgraph
"""

import argparse
import asyncio
import json
import os
from typing import Any, Dict, List

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


# === Mock Tools ===

@tool
def mock_search(query: str) -> str:
    """Search the web for information. Returns JSON with search results."""
    # Simulate realistic search API response with JSON
    results = {
        "query": query,
        "follow_up_questions": None,
        "answer": None,
        "images": [],
        "results": [
            {
                "url": "https://example.com/result1",
                "title": f"Search Result 1 for '{query}'",
                "content": f"This is detailed content about {query}. Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "score": 0.95,
                "raw_content": None
            },
            {
                "url": "https://example.com/result2",
                "title": f"Search Result 2 for '{query}'",
                "content": f"Additional information about {query}. Ut enim ad minim veniam, quis nostrud exercitation.",
                "score": 0.87,
                "raw_content": None
            }
        ]
    }
    return json.dumps(results, indent=2)


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Returns the result as a string."""
    try:
        # Safe eval for basic math
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error evaluating expression: {e}"


@tool
def get_weather(city: str) -> str:
    """Get current weather for a city. Returns JSON with weather data."""
    weather_data = {
        "city": city,
        "temperature": "72°F",
        "conditions": "Sunny",
        "humidity": "45%",
        "wind": "10 mph NW",
        "forecast": f"It's a beautiful day in {city}!"
    }
    return json.dumps(weather_data, indent=2)


# === Color Utilities ===

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def color_text(text: str, color: str) -> str:
    """Wrap text in color codes."""
    return f"{color}{text}{Colors.ENDC}"


# === Streaming Logic ===

async def stream_agent_messages(
    agent,
    query: str,
    stream_modes: List[str],
    verbose: bool = False,
    raw: bool = False
):
    """Stream agent execution and log all chunks."""

    print(color_text(f"\n{'='*80}", Colors.HEADER))
    print(color_text(f"STREAMING WITH MODE: {stream_modes}", Colors.HEADER))
    print(color_text(f"QUERY: {query}", Colors.HEADER))
    print(color_text(f"{'='*80}\n", Colors.HEADER))

    input_messages = {"messages": [{"role": "user", "content": query}]}

    chunk_count = 0

    try:
        async for chunk in agent.astream(
            input_messages,
            config={"recursion_limit": 20},
            stream_mode=stream_modes,
        ):
            chunk_count += 1
            mode, data = chunk
            print(color_text(f"\n--- Chunk #{chunk_count} (mode: {mode}) ---", Colors.CYAN))
            _log_chunk(data, mode, verbose, raw=raw)

    except Exception as exc:
        print(color_text(f"\n❌ ERROR: {exc}", Colors.RED))
        raise

    print(color_text(f"\n{'='*80}", Colors.HEADER))
    print(color_text(f"TOTAL CHUNKS: {chunk_count}", Colors.HEADER))
    print(color_text(f"{'='*80}\n", Colors.HEADER))


def _log_chunk(chunk: Any, stream_mode: str, verbose: bool, raw: bool = False):
    """Log details about a single chunk."""

    # Raw mode: just print the chunk with color based on mode
    if raw:
        # Color mapping for different stream modes
        mode_colors = {
            "messages": Colors.GREEN,
            "updates": Colors.GREEN,
            "values": Colors.CYAN,
            "custom": Colors.CYAN,
        }
        color = mode_colors.get(stream_mode, Colors.YELLOW)
        print(color_text(f"{chunk}", color))
        return

    if stream_mode == "messages":
        # chunk is (message, metadata) tuple
        message, metadata = chunk

        # Extract metadata
        node_name = metadata.get("langgraph_node", "unknown")

        # Determine message type and color
        msg_type = type(message).__name__
        if node_name == "tools":
            color = Colors.YELLOW
        elif "AI" in msg_type:
            color = Colors.GREEN
        elif "Human" in msg_type:
            color = Colors.BLUE
        else:
            color = Colors.CYAN

        print(color_text(f"Node: {node_name}", color))
        print(color_text(f"Message Type: {msg_type}", color))

        # Extract content
        if hasattr(message, "content"):
            content = str(message.content)
            if content:
                # Truncate long content unless verbose
                display_content = content if verbose else content[:200]
                if len(content) > 200 and not verbose:
                    display_content += color_text(" ... (truncated, use --verbose)", Colors.YELLOW)
                print(color_text(f"Content: {display_content}", color))
            else:
                print(color_text("Content: <empty>", Colors.YELLOW))

        # Show content_blocks if available
        if hasattr(message, "content_blocks") and verbose:
            print(color_text(f"Content Blocks: {message.content_blocks}", color))

        # Show metadata in verbose mode
        if verbose:
            print(color_text(f"Metadata: {metadata}", Colors.CYAN))

    elif stream_mode == "updates":
        # chunk is dict like {'node_name': {'messages': [...]}}
        for node_name, data in chunk.items():
            print(color_text(f"Node: {node_name}", Colors.GREEN))
            messages = data.get("messages", [])
            print(color_text(f"Messages: {len(messages)}", Colors.GREEN))
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                content = str(msg.content) if hasattr(msg, "content") else str(msg)
                display_content = content if verbose else content[:200]
                if len(content) > 200 and not verbose:
                    display_content += color_text(" ... (truncated)", Colors.YELLOW)
                print(color_text(f"  [{i}] {msg_type}: {display_content}", Colors.GREEN))
                if hasattr(msg, "content_blocks") and verbose:
                    print(color_text(f"  [{i}] Content Blocks: {msg.content_blocks}", Colors.YELLOW))

    elif stream_mode == "values":
        # chunk is the full graph state dict at each step
        if verbose:
            print(color_text(f"Graph State: {chunk}", Colors.CYAN))

        # Try to extract some structure if it's a dict
        if isinstance(chunk, dict):
            print(color_text(f"State Keys: {list(chunk.keys())}", Colors.CYAN))

            # If there's a messages key, show count
            if "messages" in chunk:
                messages = chunk["messages"]
                if isinstance(messages, list):
                    print(color_text(f"Messages Count: {len(messages)}", Colors.CYAN))
                    # Show last message if available and not too verbose
                    if messages and not verbose:
                        last_msg = messages[-1]
                        msg_type = type(last_msg).__name__
                        content = str(last_msg.content) if hasattr(last_msg, "content") else str(last_msg)
                        display = content[:100] + "..." if len(content) > 100 else content
                        print(color_text(f"Last Message ({msg_type}): {display}", Colors.CYAN))

    elif stream_mode == "custom":
        # chunk is arbitrary user data
        print(color_text(f"Custom data: {chunk}", Colors.CYAN))

    else:
        # Unknown stream mode
        print(color_text(f"Unknown mode '{stream_mode}': {chunk}", Colors.YELLOW))


# === Main ===

async def main():
    parser = argparse.ArgumentParser(
        description="Debug LangChain agent streaming behavior"
    )
    parser.add_argument(
        "--stream-mode",
        type=str,
        default="messages",
        help="Stream mode(s) to use: messages, updates, values, custom, or comma-separated list (default: messages)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Search for news about AI agents and tell me about it",
        help="Query to send to the agent"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show full content and metadata for each chunk"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw chunk output only, without structured parsing (useful for feeding to coding agents)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="o4-mini",
        help="OpenAI model to use (default: o4-mini)"
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default=None,
        help="API base URL (default: uses OPENAI_BASE_URL env var or OpenAI default)"
    )

    args = parser.parse_args()

    # Parse stream modes
    stream_modes = [m.strip() for m in args.stream_mode.split(",")]

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(color_text("❌ ERROR: OPENAI_API_KEY environment variable not set", Colors.RED))
        print("Please set it with: export OPENAI_API_KEY=your-key-here")
        return

    # Get base URL (priority: CLI arg > env var > default)
    base_url = args.api_base or os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")

    # Build model
    print(color_text(f"\n🤖 Initializing model: {args.model}", Colors.BLUE))
    if base_url:
        print(color_text(f"🌐 Using API base: {base_url}", Colors.BLUE))
        model = ChatOpenAI(
            model=args.model,
            temperature=0.7,
            api_key=api_key,
            base_url=base_url
        )
    else:
        model = ChatOpenAI(model=args.model, temperature=0.7, api_key=api_key)

    # Build tools
    tools = [mock_search, calculator, get_weather]
    print(color_text(f"🔧 Available tools: {[t.name for t in tools]}", Colors.BLUE))

    # Build agent using create_agent (same as LangChainAgentFlow)
    print(color_text("🏗️  Building agent graph with create_agent...", Colors.BLUE))
    system_prompt = (
        "You are a helpful assistant with access to tools. "
        "Use the search tool when you need current information. "
        "Use the calculator for math. Use get_weather for weather queries."
    )
    agent = create_agent(model, tools, system_prompt=system_prompt)

    # Stream and log
    await stream_agent_messages(agent, args.query, stream_modes, args.verbose, args.raw)


if __name__ == "__main__":
    asyncio.run(main())
