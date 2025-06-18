#!/bin/bash

# Setup script for SLURM MCP Server with uv

echo "Setting up SLURM MCP Server with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

# Install dependencies
echo "Installing dependencies with uv..."
uv sync

# Make the main script executable
chmod +x slurm_mcp_server.py
chmod +x test_commands.py
chmod +x example_usage.py
chmod +x debug_commands.py

echo "Setup complete! You can now:"
echo ""
echo "1. Run the server:"
echo "   uv run python slurm_mcp_server.py"
echo ""
echo "2. Test the commands:"
echo "   uv run python test_commands.py"
echo ""
echo "3. Debug the commands:"
echo "   uv run python debug_commands.py"
echo ""
echo "4. Run the example usage:"
echo "   uv run python example_usage.py"
echo ""
echo "5. Or from the parent directory:"
echo "   uv run python /path/to/slurm_mcp/slurm_mcp_server.py" 