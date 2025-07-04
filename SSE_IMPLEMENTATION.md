# Kibana MCP Server - Dual Transport Mode Implementation

## Overview

The Kibana MCP server now supports two transport modes:

1. **STDIO Mode (Default)** - Standard MCP transport for use with MCP clients like Claude Desktop
2. **SSE Mode** - HTTP Server-Sent Events endpoint for web applications

## Configuration

### Environment Variables

- `MCP_TRANSPORT` - Transport mode ("stdio" or "sse"), defaults to "stdio"
- `MCP_SSE_HOST` - SSE server host, defaults to "127.0.0.1"
- `MCP_SSE_PORT` - SSE server port, defaults to "8000"

### Running the Server

#### STDIO Mode (Default)

```bash
# Default mode - no additional configuration needed
python -m kibana_mcp

# Explicitly set STDIO mode
MCP_TRANSPORT=stdio python -m kibana_mcp
```

#### SSE Mode

```bash
# Basic SSE mode
MCP_TRANSPORT=sse python -m kibana_mcp

# Custom host and port
MCP_TRANSPORT=sse MCP_SSE_HOST=0.0.0.0 MCP_SSE_PORT=9000 python -m kibana_mcp

# Using the convenience script
./run_sse_server.py

# Using Make target
make dev-sse
```

## SSE Endpoint

When running in SSE mode, the server exposes:

- **SSE Endpoint**: `http://host:port/sse` - For SSE connections
- **Messages Endpoint**: `http://host:port/messages` - For POST requests

## Files Added/Modified

### Modified Files

- `src/kibana_mcp/server.py` - Added dual transport mode support
- `README.md` - Added SSE documentation
- `Makefile` - Added `dev-sse` target

### New Files

- `run_sse_server.py` - Convenience script to run SSE server
- `example_sse_usage.py` - Example showing how to use the SSE endpoint
- `test_sse.py` - Simple test script for SSE connectivity

## Usage Examples

### Running SSE Server

```bash
# Start SSE server with environment variables
export KIBANA_URL="https://your-kibana.example.com:5601"
export KIBANA_API_KEY="your_base64_api_key"
export MCP_TRANSPORT="sse"

python -m kibana_mcp
# Server will be available at http://127.0.0.1:8000/sse
```

### Testing SSE Connectivity

```bash
# Test if SSE server is running
python test_sse.py

# Show example MCP requests
python example_sse_usage.py

# Test with requests library (if available)
python example_sse_usage.py --test
```

### Docker SSE Deployment

```bash
# Run SSE server in Docker
docker run -p 8000:8000 \
  -e MCP_TRANSPORT="sse" \
  -e MCP_SSE_HOST="0.0.0.0" \
  -e KIBANA_URL \
  -e KIBANA_API_KEY \
  ghcr.io/jamesagarside/kibana-mcp:latest
```

## Implementation Details

The implementation uses FastMCP 0.4.1's built-in SSE support:

- STDIO mode uses `mcp.run(transport="stdio")`
- SSE mode configures `mcp.settings.host` and `mcp.settings.port`, then calls `asyncio.run(mcp.run_sse_async())`

The SSE server uses Starlette and Uvicorn under the hood, providing a production-ready HTTP server for MCP protocol communication.

## Stateless Architecture

The SSE implementation follows a completely stateless design pattern, making it ideal for:

- **Cloud Run deployments**: No server-side session state to be lost during scaling or container restarts
- **N8N agent workflows**: Handle multiple concurrent short-lived connections
- **Horizontal scaling**: Deploy multiple instances without session state concerns
- **High availability**: No single point of failure due to session state

### Key Implementation Features

1. **No In-Memory Sessions**: Each request is self-contained with its own context
2. **Connection Pooling**: Efficient HTTP client connection reuse
3. **Short Timeouts**: Optimized for quick agent interactions
4. **Minimal Memory Footprint**: No large in-memory session storage

This stateless approach eliminates the previous issues with session loss that could occur during:

- Container restarts
- Auto-scaling events
- Connection interruptions

For deployment on Google Cloud Run, see [CLOUD_RUN_SESSION_FIXES.md](CLOUD_RUN_SESSION_FIXES.md).
