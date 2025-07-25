# Kibana MCP Server

![Kibana MCP Demo](faster-server-demo.gif)

Model Context Protocol (MCP) server for Kibana Security - manage alerts, rules, exceptions, saved objects, and endpoints via AI assistants.

## Quick Start

### 1. Configure MCP Cli

**Option A: Using Environment Variables (Recommended)**

First, set your credentials:

```bash
export KIBANA_URL="https://your-kibana.example.com:5601"

# Option 1: API Key (recommended)
export KIBANA_API_KEY="your_base64_api_key"

# Option 2: Username/Password
# export KIBANA_USERNAME="your_username"
# export KIBANA_PASSWORD="your_password"
```

Then add to your MCP config:

```json
{
  "mcpServers": {
    "kibana-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "host",
        "-e",
        "KIBANA_URL",
        "-e",
        "KIBANA_API_KEY",
        "ghcr.io/jamesagarside/kibana-mcp:latest"
      ]
    }
  }
}
```

For username/password, use:

```json
{
  "mcpServers": {
    "kibana-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "host",
        "-e",
        "KIBANA_URL",
        "-e",
        "KIBANA_USERNAME",
        "-e",
        "KIBANA_PASSWORD",
        "ghcr.io/jamesagarside/kibana-mcp:latest"
      ]
    }
  }
}
```

**Option B: Direct Credentials (Easier for Claude Desktop)**

Using API Key:

```json
{
  "mcpServers": {
    "kibana-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "host",
        "-e",
        "KIBANA_URL=https://your-kibana.example.com:5601",
        "-e",
        "KIBANA_API_KEY=your_base64_api_key",
        "ghcr.io/jamesagarside/kibana-mcp:latest"
      ]
    }
  }
}
```

Using Username/Password:

```json
{
  "mcpServers": {
    "kibana-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "host",
        "-e",
        "KIBANA_URL=https://your-kibana.example.com:5601",
        "-e",
        "KIBANA_USERNAME=your_username",
        "-e",
        "KIBANA_PASSWORD=your_password",
        "ghcr.io/jamesagarside/kibana-mcp:latest"
      ]
    }
  }
}
```

_Note: Option B is less secure but more convenient for tools like Claude Desktop where environment variables are harder to manage._

### Build yourself

If you'd rather not use the public image you can build this MCP server yourself.

```bash
git clone https://github.com/jamesagarside/kibana-mcp.git
cd kibana-mcp
make build
```

### Running as SSE Server

This MCP server supports two transport modes:

1. **STDIO Mode (default)** - Standard MCP transport for use with MCP clients
2. **SSE Mode** - HTTP Server-Sent Events endpoint for web applications

#### STDIO Mode (Default)

The server runs in STDIO mode by default, suitable for MCP clients like Claude Desktop:

```bash
# Using Docker
docker run -i --rm -e KIBANA_URL -e KIBANA_API_KEY ghcr.io/jamesagarside/kibana-mcp:latest

# Using Python
python -m kibana_mcp
```

#### SSE Mode

To run as an SSE server, set the `MCP_TRANSPORT` environment variable:

```bash
# Set environment variables
export MCP_TRANSPORT="sse"
export MCP_SSE_HOST="127.0.0.1"  # Optional, defaults to 127.0.0.1
export MCP_SSE_PORT="8000"       # Optional, defaults to 8000

# Run the server
python -m kibana_mcp
```

Or use the convenience script:

```bash
# Using the convenience script
./run_sse_server.py

# Or with custom host/port
MCP_SSE_HOST="0.0.0.0" MCP_SSE_PORT="9000" ./run_sse_server.py
```

The SSE endpoint will be available at `http://127.0.0.1:8000/sse` (or your configured host/port).

#### Docker SSE Deployment

```bash
# Run SSE server in Docker
docker run -p 8000:8000 \
  -e MCP_TRANSPORT="sse" \
  -e MCP_SSE_HOST="0.0.0.0" \
  -e KIBANA_URL \
  -e KIBANA_API_KEY \
  ghcr.io/jamesagarside/kibana-mcp:latest
```

Then access the SSE endpoint at `http://localhost:8000/sse`.

### Testing SSE Mode

To test that the SSE server is working correctly, you can use the provided test scripts:

```bash
# Quick test - verifies server starts and is listening
make test-sse

# Or run directly
./test_minimal.py

# Demonstration test showing SSE streaming
./test_sse_working.py
```

The minimal test will:

1. Start the MCP server in SSE mode
2. Verify it's listening on the correct port
3. Confirm the SSE endpoint is accessible
4. Clean up the server process

## Available Tools

### Alert Management

- **`get_alerts`** - Fetch security alerts
- **`tag_alert`** - Add tags to alerts
- **`adjust_alert_status`** - Change alert status (open/acknowledged/closed)

### Rule Management

- **`find_rules`** - Search detection rules
- **`get_rule`** - Retrieve details of a specific rule
- **`delete_rule`** - Delete a detection rule
- **`update_rule_status`** - Enable or disable a rule
- **`get_prepackaged_rules_status`** - Check status of Elastic's prepackaged rules
- **`install_prepackaged_rules`** - Install/update Elastic's prepackaged rules

### Exception Management

- **`get_rule_exceptions`** - Get rule exception items
- **`add_rule_exception_items`** - Add exceptions to rules
- **`create_exception_list`** - Create new exception lists
- **`associate_shared_exception_list`** - Link exception lists to rules

### Cases Management

- **`find_cases`** - Search for cases based on various criteria
- **`get_case`** - Get detailed information about a specific case
- **`create_case`** - Create a new case
- **`update_case`** - Update an existing case
- **`delete_cases`** - Delete one or more cases
- **`add_case_comment`** - Add a comment or alert to a case
- **`get_case_comments`** - Get comments and alerts for a specific case
- **`get_case_alerts`** - Get all alerts attached to a specific case
- **`get_cases_by_alert`** - Get all cases that contain a specific alert
- **`get_case_configuration`** - Get case configuration settings
- **`get_case_tags`** - Get all case tags

### Saved Objects Management

- **`find_objects`** - Search for saved objects (dashboards, visualizations, etc.)
- **`get_object`** - Retrieve details of a specific saved object
- **`bulk_get_objects`** - Get multiple saved objects in a single request
- **`create_object`** - Create a new saved object
- **`update_object`** - Update an existing saved object
- **`delete_object`** - Delete a saved object
- **`export_objects`** - Export saved objects to NDJSON format
- **`import_objects`** - Import saved objects from NDJSON format

### Endpoint Management

- **`isolate_endpoint`** - Isolate one or more endpoints from the network
- **`unisolate_endpoint`** - Release one or more endpoints from isolation
- **`run_command_on_endpoint`** - Run a shell command on one or more endpoints
- **`get_response_actions`** - Get a list of response actions from endpoints
- **`get_response_action_details`** - Get details of a specific response action
- **`get_response_action_status`** - Get status of response actions
- **`kill_process`** - Terminate a running process on an endpoint
- **`suspend_process`** - Suspend a running process on an endpoint
- **`scan_endpoint`** - Scan a file or directory on an endpoint for malware
- **`get_file_info`** - Get information for a file retrieved by a response action
- **`download_file`** - Download a file from an endpoint

## Local Development

### Manual Development

If you prefer not to use the Makefile, you can also run the commands manually:

```bash
# Install dependencies
uv sync

# Set environment variables (see above)

# Run locally
uv run kibana-mcp
```

### Project Structure

The project is organized into the following structure:

```
src/kibana_mcp/
├── tools/
│   ├── alerts/       # Tools for managing alerts
│   ├── rules/        # Tools for managing rules
│   ├── exceptions/   # Tools for managing exception lists
│   ├── endpoint/     # Tools for endpoint management and response actions
│   ├── saved_objects/ # Tools for managing saved objects (dashboards, visualizations, etc.)
│   └── utils/        # Utility functions
├── models/           # Pydantic models
├── server.py         # MCP server implementation
├── prompts.py        # Custom prompts
└── resources.py      # Resource handlers
```

### Testing Code

#### Complete Unit Tests and Coverage Test

```bash
make test
```

#### Granular Testing

The recommended way to run tests is using the Makefile:

```bash
# Run all tests with coverage
make test

# Run pytest without coverage
make run-pytest
```

If you need to test specific modules or test files, you can use pytest directly after activating the virtual environment:

```bash
# Activate the virtual environment created by the Makefile
source .venv/bin/activate

# Run tests for a specific category
PYTHONPATH=./src pytest -xvs testing/tools/alerts/test_alert_tools.py
PYTHONPATH=./src pytest -xvs testing/tools/rules/test_rule_tools.py
PYTHONPATH=./src pytest -xvs testing/tools/exceptions/test_exception_tools.py
PYTHONPATH=./src pytest -xvs testing/tools/endpoint/test_endpoint_tools.py
PYTHONPATH=./src pytest -xvs testing/tools/saved_objects/test_saved_objects.py
```

### Testing MCP Server Locally

The Makefile provides commands to help you set up a complete test environment with Elastic Stack using Docker. This environment will be bootstrapped with sample data for testing.

### Setting Up the Test Environment

```bash
# Install required tools
make install-elastic-package

# Start the complete test environment (Elasticsearch, Kibana, Fleet Server and Agent)
make start-test-env

# Access Kibana at http://localhost:5601
# Username: elastic
# Password: elastic

# When finished, stop the test environment
make stop-test-env
```

Once your test environment is running, you can test the MCP server with any MCP-compatible LLM client (like Claude Desktop, Cursor, etc.).

After setup, you can verify the connection by:

1. Going to Kibana at https://localhost:5601 and login using the username: `elastic` and password: `changeme`
2. Navigate to Management > Fleet
3. Verify the Fleet Server and Agent are connected and healthy

### Configure Claude Desktop

```json
{
  "mcpServers": {
    "kibana-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "host",
        "-e",
        "KIBANA_URL=https://localhost:5601",
        "-e",
        "KIBANA_USERNAME=elastic",
        "-e",
        "KIBANA_PASSWORD=changeme",
        "kibana-mcp"
      ]
    }
  }
}
```

The project includes a comprehensive Makefile to help with common development tasks. You can view all available commands with:

```bash
make help
```

### Using the Makefile

The Makefile includes the following main categories of commands:

#### Development Commands

```bash
# Run the server locally in development mode (sets up local Kibana connection)
make dev

# Build the Docker image
make build
```

#### Testing Commands

```bash
# Run all tests (pytest and coverage)
make test

# Run pytest only
make run-pytest

# Run tests with coverage reporting
make run-coverage

# Test SSE server locally
make test-sse
```

#### Test Environment Commands

```bash
# Install the elastic-package tool
make install-elastic-package

# Start the complete test environment
make start-test-env

# Start only the Elastic Stack containers
make start-elastic-stack

# Configure the test environment
make configure-test-env

# Stop the test environment
make stop-test-env
```

## Deployment on Cloud Run

The server uses a completely stateless architecture, making it ideal for cloud deployments like Google Cloud Run and for integrating with automation tools like N8N.

### Stateless Architecture Benefits

- **No Session State**: Each request is self-contained, eliminating session loss concerns
- **Scale to Zero**: Minimize costs when idle (autoscaling.knative.dev/minScale: "0")
- **High Concurrency**: Support 1000+ concurrent requests
- **Efficient Connection Pooling**: Optimized for short-lived connections

### Cloud Run Deployment

A simple deployment script is provided:

```bash
# Set your GCP project ID and region
export PROJECT_ID="your-project-id"
export REGION="europe-west2"

# Run the deployment script
./deploy-cloud-run.sh
```

For detailed information on the stateless architecture and optimizations for Cloud Run, see [CLOUD_RUN_SESSION_FIXES.md](CLOUD_RUN_SESSION_FIXES.md).

### N8N Integration

For integrating with N8N automation workflows, refer to the [N8N Integration Guide](N8N_INTEGRATION_GUIDE.md).
