# SSE MCP Server Testing Guide

This document describes the various test scripts available for testing the Kibana MCP server in SSE mode.

## Available Test Scripts

### 1. `test_minimal.py` - Basic Connectivity Test

**Purpose**: Quick verification that the SSE server starts and is listening.

```bash
./test_minimal.py
# or
make test-sse
```

**What it tests**:

- ✅ Server starts in SSE mode
- ✅ Port is open and accepting connections
- ✅ Process remains stable

**Use when**: You just want to verify the server starts correctly.

### 2. `test_sse_simple.py` - Standard Library HTTP Test

**Purpose**: Tests HTTP endpoints using only Python standard library.

```bash
./test_sse_simple.py
```

**What it tests**:

- ✅ Basic HTTP connectivity
- ✅ Server responds to requests
- ⚠️ MCP request handling (may show expected errors)

**Use when**: You want to test without external dependencies.

### 3. `test_sse_advanced.py` - Comprehensive HTTP Test

**Purpose**: Detailed testing of all HTTP endpoints and MCP protocol.

```bash
./test_sse_advanced.py
```

**What it tests**:

- ✅ All HTTP endpoints (`/`, `/sse`, `/messages`)
- ✅ SSE connection handling
- ⚠️ MCP message protocol
- ✅ Response codes and content types

**Use when**: You want detailed endpoint analysis.

### 4. `test_sse_local.py` - Full MCP Protocol Test

**Purpose**: Complete MCP protocol testing with requests library.

```bash
./test_sse_local.py
```

**Requirements**: `requests` library (auto-installed if missing)

**What it tests**:

- ✅ Full MCP protocol implementation
- ✅ Tools listing
- ✅ Resources listing
- ✅ Prompts listing
- ⚠️ Actual Kibana operations (may fail without real Kibana)

**Use when**: You want to test the complete MCP implementation.

## Test Results Summary

Based on our testing, the SSE server implementation:

### ✅ Working Features

- Server starts correctly in SSE mode
- Listens on configured host/port
- `/sse` endpoint available with correct content-type
- Server-Sent Events protocol supported
- Process management works (start/stop)

### ⚠️ Expected Behaviors

- `/` returns 404 (no root endpoint defined)
- MCP requests may fail without real Kibana connection
- Some protocol errors are expected during testing

### 🎯 Successful Tests

1. **Server Startup**: All tests confirm server starts correctly
2. **Port Binding**: Server binds to correct host:port
3. **SSE Endpoint**: `/sse` endpoint available with proper headers
4. **Process Management**: Clean startup and shutdown

## Environment Variables for Testing

All tests use these environment variables:

```bash
export MCP_TRANSPORT="sse"
export MCP_SSE_HOST="127.0.0.1"    # Optional, defaults to 127.0.0.1
export MCP_SSE_PORT="8000"         # Optional, defaults to 8000
export KIBANA_URL="http://localhost:5601"  # For actual Kibana testing
export KIBANA_USERNAME="test"      # Test credentials
export KIBANA_PASSWORD="test"      # Test credentials
```

## Running Tests

### Quick Test

```bash
make test-sse
```

### All Tests

```bash
./test_minimal.py      # Basic
./test_sse_simple.py   # Standard library
./test_sse_advanced.py # Comprehensive
./test_sse_local.py    # Full MCP (requires requests)
```

### With Real Kibana

```bash
export KIBANA_URL="https://your-kibana.example.com:5601"
export KIBANA_API_KEY="your_api_key"
./test_sse_local.py
```

## Test Output Interpretation

### ✅ Success Indicators

- "Server is ready"
- "Server is listening on host:port"
- "200 OK" responses
- "text/event-stream" content-type

### ⚠️ Expected Warnings

- "404 Not Found" for root endpoint
- "Method Not Allowed" for wrong HTTP methods
- "Connection errors" without real Kibana

### ❌ Actual Failures

- Server process dies during startup
- Port binding failures
- Timeout during server startup
- Process hanging or not responding

## Troubleshooting

### Server Won't Start

1. Check if port is already in use: `lsof -i :8000`
2. Verify Python module path: `python -m src.kibana_mcp.server`
3. Check environment variables are set correctly

### Connection Timeouts

1. Increase timeout values in test scripts
2. Check firewall settings
3. Verify host binding (0.0.0.0 vs 127.0.0.1)

### MCP Protocol Errors

1. These are often expected without real Kibana
2. Check Kibana credentials and URL
3. Verify Kibana is accessible from test environment

## Integration with CI/CD

For automated testing, use the minimal test:

```yaml
# GitHub Actions example
- name: Test SSE Server
  run: make test-sse
```

The minimal test is designed to:

- Run quickly (< 30 seconds)
- Have minimal dependencies
- Provide clear pass/fail results
- Clean up processes properly
