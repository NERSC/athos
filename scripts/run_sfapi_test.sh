#!/bin/bash

source .env
export NERSC_CLIENT_ID
export NERSC_PRIVATE_KEY_PATH

# Test direct server launch
timeout 10s nersc-sfapi-mcp

# Test standalone server with FastMCP client
python src/athos/examples/sfapi_client_test.py
