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
