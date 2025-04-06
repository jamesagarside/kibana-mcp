# Kibana MCP Server

This project provides a Model Context Protocol (MCP) server implementation that allows AI assistants to interact with Kibana Security alerts.

## Features

This server exposes the following tools to MCP clients:

### Tools

*   **`tag_alert`**: Adds one or more tags to a specific Kibana security alert signal.
    *   `alert_id` (string, required): The ID of the Kibana alert signal to tag.
    *   `tags` (array of strings, required): A list of tags to add to the alert signal.
*   **`adjust_alert_status`**: Changes the status of a specific Kibana security alert signal.
    *   `alert_id` (string, required): The ID of the Kibana alert signal.
    *   `new_status` (string, required): The new status. Must be one of: "open", "acknowledged", "closed".
*   **`get_alerts`**: Fetches recent Kibana security alert signals, optionally filtering by text and limiting quantity.
    *   `limit` (integer, optional, default: 20): Maximum number of alerts to return.
    *   `search_text` (string, optional): Text to search for in alert signal fields.

## Configuration

To connect to your Kibana instance, the server requires the following environment variables to be set:

*   `KIBANA_URL`: The base URL of your Kibana instance (e.g., `https://your-kibana.example.com:5601`).

And **one** of the following authentication methods:

*   **API Key (Recommended):**
    *   `KIBANA_API_KEY`: A Base64 encoded Kibana API key. Generate this in Kibana under Stack Management -> API Keys. Ensure the key has permissions to read and update security alerts/signals (e.g., appropriate privileges for the Security Solution feature).
    *   Example format: `VzR1dU5COXdPUTRhQVZHRWw2bkk6LXFSZGRIVGNRVlN6TDA0bER4Z1JxUQ==` (This is just an example, use your actual key).
*   **Username/Password (Less Secure):**
    *   `KIBANA_USERNAME`: Your Kibana username.
    *   `KIBANA_PASSWORD`: Your Kibana password.

The server prioritizes `KIBANA_API_KEY` if it is set. If it's not set, it will attempt to use `KIBANA_USERNAME` and `KIBANA_PASSWORD`.

## Quickstart: Running the Server

1.  Set the required environment variables (`KIBANA_URL` and authentication variables).

    *   **Using API Key:**
        ```bash
        export KIBANA_URL="<your_kibana_url>"
        export KIBANA_API_KEY="<your_base64_encoded_api_key>"
        ```
    *   **Using Username/Password:**
        ```bash
        export KIBANA_URL="<your_kibana_url>"
        export KIBANA_USERNAME="<your_kibana_username>"
        export KIBANA_PASSWORD="<your_kibana_password>"
        ```

2.  Navigate to the project directory (`kibana-mcp`).
3.  Run the server using `uv` (which uses the entry point defined in `pyproject.toml`):

    ```bash
    uv run kibana-mcp
    ```

The server will start and listen for MCP connections via standard input/output.

## Connecting an MCP Client (e.g., Cursor, Claude Desktop)

You can configure MCP clients like Cursor or Claude Desktop to use this server.

**Configuration File Locations:**

*   Cursor: `~/.cursor/mcp.json`
*   Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows)

Add the following server configuration under the `mcpServers` key, replacing `/path/to/kibana-mcp` with the actual absolute path to your project root. Choose **one** authentication method (`KIBANA_API_KEY` or `KIBANA_USERNAME`/`KIBANA_PASSWORD`) within the command arguments.

**Recommended Configuration (using `/usr/bin/env`):**

Some client applications may not reliably pass environment variables defined in their configuration's `env` block. Using `/usr/bin/env` directly ensures the variables are set for the server process.

```json
{
  "mcpServers": {
    "kibana-mcp": { // You can choose any name for the client to display
      "command": "/usr/bin/env", // Use env command for reliability
      "args": [
        // Set required environment variables here
        "KIBANA_URL=<your_kibana_url>",

        // Option 1: API Key (Recommended)
        "KIBANA_API_KEY=<your_base64_encoded_api_key>",

        // Option 2: Username/Password (Mutually exclusive with API Key)
        // "KIBANA_USERNAME=<your_kibana_username>",
        // "KIBANA_PASSWORD=<your_kibana_password>",

        // Command to run the server (using absolute paths)
        "/path/to/your/virtualenv/bin/python", // e.g., /Users/me/kibana-mcp/.venv/bin/python
        "/path/to/kibana-mcp/src/kibana_mcp/server.py" // Absolute path to server script
      ],
      "options": {
          "cwd": "/path/to/kibana-mcp" // Set correct working directory
          // No "env" block needed here when using /usr/bin/env in command/args
      }
    }
    // Add other servers here if needed
  }
}
```

*(Note: Replace placeholders like `<your_kibana_url>`, `<your_base64_encoded_api_key>`, and the python/script paths with your actual values. Storing secrets directly in the config file is generally discouraged for production use. Consider more secure ways to manage environment variables if needed.)*

**Alternative Configuration (Standard `env` block - might not work reliably):**

*(This is the standard documented approach but proved unreliable in some environments)*

```json
{
  "mcpServers": {
    "kibana-mcp-alt": { 
      "command": "/path/to/your/virtualenv/bin/python", 
      "args": [
        "/path/to/kibana-mcp/src/kibana_mcp/server.py"
      ],
      "options": {
          "cwd": "/path/to/kibana-mcp",
          // Choose one auth method:
          "KIBANA_API_KEY": "<your_base64_encoded_api_key>"
          // OR
          // "KIBANA_USERNAME": "<your_kibana_username>",
          // "KIBANA_PASSWORD": "<your_kibana_password>"
      }
    }
  }
}
```

## Development

### Installing Dependencies

Sync dependencies using `uv`:

```bash
uv sync
```

### Building and Publishing

To prepare the package for distribution:

1.  Build package distributions:
    ```bash
    uv build
    ```
    This will create source and wheel distributions in the `dist/` directory.

2.  Publish to PyPI:
    ```bash
    uv publish
    ```
    Note: You'll need to configure PyPI credentials.

## Local Development & Testing Environment

The `testing/` directory contains scripts and configuration to spin up local Elasticsearch and Kibana instances using Docker Compose and automatically seed them with a sample detection rule.

**Prerequisites:**

*   [Python 3](https://www.python.org/)
*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)
*   Python dependencies for testing scripts: Install using
    ```bash
    pip install -r requirements-dev.txt
    ```

**Quickstart:**

1.  Install development dependencies:
    ```bash
    pip install -r requirements-dev.txt
    ```
2.  Run the quickstart script from the project root directory:
    ```bash
    ./testing/quickstart-test-env.sh
    ```
3.  The script (`testing/main.py`) will perform checks, start the containers, wait for services, create a sample **detection rule**, write sample auth data, verify signal generation, and print the access URLs/credentials.
4.  Access Kibana at `http://localhost:5601` (User: `elastic`, Pass: `elastic`). The internal user Kibana connects with is `kibana_system_user`.

**Manual Steps (Overview):**

The `testing/quickstart-test-env.sh` script executes `python -m testing.main`. This Python script performs the following:
1.  Checks for Docker & Docker Compose.
2.  Parses `testing/docker-compose.yml` for configuration.
3.  Runs `docker compose up -d`.
4.  Waits for Elasticsearch and Kibana APIs.
5.  Creates a custom user (`kibana_system_user`) and role for Kibana's internal use.
6.  Creates an index template (`mcp_auth_logs_template`).
7.  Reads `testing/sample_rule.json` (a detection rule).
8.  Sends a POST request to `http://localhost:5601/api/detection_engine/rules` to create the rule.
9.  Writes sample data from `testing/auth_events.ndjson` to `mcp-auth-logs-default` index.
10. Checks for detection signals using `http://localhost:5601/api/detection_engine/signals/search`.
11. Prints status, URLs, credentials, and shutdown commands.

**Stopping the Test Environment:**

*   Run the shutdown command printed by the script (e.g., `docker compose -f testing/docker-compose.yml down`). Use the `-v` flag (`down -v`) to remove data volumes if needed.