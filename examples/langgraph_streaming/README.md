# ATHOS Examples

This directory contains standalone examples for testing and understanding ATHOS components.

## Streaming Debug Script

**File:** `streaming_debug.py`

A standalone script to debug LangChain agent streaming behavior without ATHOS dependencies. Uses the same `create_agent` pattern as `LangChainAgentFlow`.

### Setup

```bash
# Install dependencies
pip install langchain langchain-openai langgraph

# Set API key
export OPENAI_API_KEY=your-key-here
```

### Usage

```bash
# Basic usage (stream_mode="messages" by default)
python examples/streaming_debug.py

# Test different stream modes
python examples/streaming_debug.py --stream-mode updates
python examples/streaming_debug.py --stream-mode values
python examples/streaming_debug.py --stream-mode messages,updates

# Custom query
python examples/streaming_debug.py --query "What's 123 * 456?"

# Verbose mode (shows full content and metadata)
python examples/streaming_debug.py --verbose

# Raw mode (print only raw chunks, useful for feeding to coding agents)
python examples/streaming_debug.py --raw

# Use different model
python examples/streaming_debug.py --model gpt-4
```

### What It Does

1. **Creates simple mock tools** that return JSON (like real APIs do):
   - `mock_search`: Returns search results JSON
   - `calculator`: Evaluates math expressions
   - `get_weather`: Returns weather data JSON

2. **Uses `create_agent`** exactly like `LangChainAgentFlow` does

3. **Streams with different modes**:
   - `messages`: Token-by-token LLM output + tool messages
   - `updates`: State updates after each agent step
   - `values`: Full graph state dict at each step
   - `custom`: User-defined custom events

4. **Color-coded output**:
   - 🟢 Green: AI/model node messages
   - 🟡 Yellow: Tool node messages (the raw JSON we were filtering out)
   - 🔵 Blue: Human messages
   - 🔴 Red: Full chunk, Errors

### Debugging the Recent Issue

The raw JSON issue we just fixed can be reproduced and debugged with:

```bash
# This will show tool node messages in YELLOW
python examples/streaming_debug.py --stream-mode messages --verbose

# Look for chunks with "Node: tools" - these contain the raw JSON
# In the ATHOS flow, we filter these out with:
#   if metadata.get("langgraph_node") == "tools": continue
```

### Example Output

See the `streaming_messages.log` and `streaming_updates.log` log files
in the `examples/` folder for example outputs.

### Tips

- Start with `--stream-mode messages` to understand token streaming
- Use `--verbose` to see all metadata and full content
- Try `--stream-mode updates` to see step-by-step agent execution
- Use `--stream-mode messages,updates` to compare both simultaneously
- Modify the mock tools to test different response formats
