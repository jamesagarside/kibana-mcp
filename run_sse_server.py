#!/usr/bin/env python3
"""
Script to run the Kibana MCP server in SSE mode.
This sets the necessary environment variables and starts the server.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def main():
    # Set SSE mode environment variables
    os.environ["MCP_TRANSPORT"] = "sse"

    # Set default host and port if not already set
    if "MCP_SSE_HOST" not in os.environ:
        os.environ["MCP_SSE_HOST"] = "127.0.0.1"

    if "MCP_SSE_PORT" not in os.environ:
        os.environ["MCP_SSE_PORT"] = "8000"

    print(f"Starting Kibana MCP Server in SSE mode...")
    print(f"Host: {os.environ['MCP_SSE_HOST']}")
    print(f"Port: {os.environ['MCP_SSE_PORT']}")
    print(
        f"URL: http://{os.environ['MCP_SSE_HOST']}:{os.environ['MCP_SSE_PORT']}")
    print()

    # Import and run the server
    from kibana_mcp.server import run_server
    run_server()


if __name__ == "__main__":
    main()
