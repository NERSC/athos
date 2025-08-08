#!/bin/bash

echo "Setting up RAG MCP Server..."

if ! command -v uv &> /dev/null; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source ~/.bashrc
fi

uv sync
chmod +x rag_mcp_server.py
