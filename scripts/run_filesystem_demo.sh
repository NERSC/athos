#!/bin/bash

# ATHOS Filesystem Demo Runner
# This script runs the ATHOS-based filesystem demonstration

echo "🚀 Starting ATHOS Filesystem Demo..."
echo "This demo shows filesystem operations using the ATHOS framework"
echo ""

# Check if required MCP server is installed
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx is not installed. Please install Node.js first."
    exit 1
fi

# Check if the MCP filesystem server package is available
echo "🔍 Checking MCP filesystem server availability..."
if ! npm list -g @modelcontextprotocol/server-filesystem &> /dev/null; then
    echo "⚠️  MCP filesystem server not found. Installing..."
    echo "This may take a moment..."
    npm install -g @modelcontextprotocol/server-filesystem
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install MCP filesystem server"
        echo "Please run: npm install -g @modelcontextprotocol/server-filesystem"
        exit 1
    fi
fi

echo "✅ MCP filesystem server is available"
echo ""

# Run the demo
ls config/
python -m athos.examples.filesystem_demo --config $PWD/config/config.yaml

echo ""
echo "📝 Demo completed! Check the 'athos_filesystem_demo' directory for created files."