#!/bin/bash

source .env

# Test direct server launch
#timeout 10s iris-mcp

# Test standalone server with FastMCP client
python src/athos/examples/iris_client_test.py
