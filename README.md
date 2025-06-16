# Kibana MCP Server

![Kibana MCP Demo](faster-server-demo.gif)

Model Context Protocol (MCP) server for Kibana Security - manage alerts, rules, and exceptions via AI assistants.

## Quick Start

### 1. Clone and Build

```bash
git clone https://github.com/ggilligan12/kibana-mcp.git
cd kibana-mcp
docker build -t kibana-mcp .
```

### 2. Configure MCP Client

Add to your MCP client config (Claude Desktop, Cursor, etc.):

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
        "kibana-mcp"
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
        "kibana-mcp"
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
        "kibana-mcp"
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
        "kibana-mcp"
      ]
    }
  }
}
```

_Note: Option B is less secure but more convenient for tools like Claude Desktop where environment variables are harder to manage._

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
- **`create_exception_list`** - Create new exception lists
- **`associate_shared_exception_list`** - Link exception lists to rules
- **`get_prepackaged_rules_status`** - Check status of Elastic's prepackaged rules
- **`install_prepackaged_rules`** - Install/update Elastic's prepackaged rules

## Local Development

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
│   └── utils/        # Utility functions
├── models/           # Pydantic models
├── server.py         # MCP server implementation
├── prompts.py        # Custom prompts
└── resources.py      # Resource handlers
```

### Running Tests

```bash
# Run all tests
PYTHONPATH=/path/to/src pytest -xvs testing/tools/test_all.py

# Run tests for a specific category
PYTHONPATH=/path/to/src pytest -xvs testing/tools/alerts/test_alert_tools.py
PYTHONPATH=/path/to/src pytest -xvs testing/tools/rules/test_rule_tools.py
PYTHONPATH=/path/to/src pytest -xvs testing/tools/exceptions/test_exception_tools.py
PYTHONPATH=/path/to/src pytest -xvs testing/tools/endpoint/test_endpoint_tools.py
```

### Test Environment

```bash
# Start local Kibana/Elasticsearch with test data
pip install -r testing/requirements-dev.txt
./testing/quickstart-test-env.sh

# Access at http://localhost:5601 (elastic/elastic)
```

### Fleet and Endpoint Testing Environment

To test the endpoint management tools with actual Elastic Fleet Server and Elastic Agent:

```bash
# Start the fully automated endpoint test environment (including Fleet and Agent)
./testing/start-endpoint-test-env.sh

# Or use the quick start script which also includes Fleet and Agent setup
./testing/quickstart-test-env.sh

# Check status
docker compose -f testing/docker-compose.yml ps
# or if you have docker-compose v1
docker-compose -f testing/docker-compose.yml ps
```

After setup, you can verify the connection by:

1. Going to Kibana at http://localhost:5601
2. Navigate to Management > Fleet
3. Verify the Fleet Server and Agent are connected and healthy
