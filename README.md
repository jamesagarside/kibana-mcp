# Kibana MCP Server

This project provides a Model Context Protocol (MCP) server implementation that allows AI assistants to interact with Kibana Security alerts.

## Features

This server exposes the following tools to MCP clients:

### Tools

*   **`tag_alert`**: Adds one or more tags to a specific Kibana security alert.
    *   `alert_id` (string, required): The ID of the Kibana alert to tag.
    *   `tags` (array of strings, required): A list of tags to add to the alert. Existing tags are preserved, and duplicates are handled.
*   **`adjust_alert_severity`**: Changes the severity of a specific Kibana security alert.
    *   `alert_id` (string, required): The ID of the Kibana alert.
    *   `new_severity` (string, required): The new severity level. Must be one of: "informational", "low", "medium", "high", "critical".

## Configuration

To connect to your Kibana instance, the server requires the following environment variables to be set:

*   `KIBANA_URL`: The base URL of your Kibana instance (e.g., `https://your-kibana.example.com:5601`).
*   `KIBANA_API_KEY`: A Kibana API key in the format `id:secret`. Generate this in Kibana under Stack Management -> API Keys. Ensure the key has permissions to read and update alerts (e.g., appropriate privileges for the Alerting plugin).

## Quickstart: Running the Server

1.  Ensure you have set the required environment variables (`KIBANA_URL`, `KIBANA_API_KEY`).
2.  Navigate to the project directory (`kibana-mcp`).
3.  Run the server using `uv` (which uses the entry point defined in `pyproject.toml`):

    ```bash
    export KIBANA_URL="<your_kibana_url>"
    export KIBANA_API_KEY="<your_api_key_id>:<your_api_key_secret>"
uv run kibana-mcp
    ```

The server will start and listen for MCP connections via standard input/output.

## Connecting an MCP Client (e.g., Claude Desktop)

You can configure MCP clients like Claude Desktop to use this server.

**Claude Desktop Configuration:**

Edit your `claude_desktop_config.json` file:

*   macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
*   Windows: `%APPDATA%/Claude/claude_desktop_config.json`

Add the following server configuration under the `mcpServers` key, replacing `/path/to/kibana-mcp` with the actual absolute path to this project directory on your system:

```json
{
  "mcpServers": {
    "kibana-security": { // You can choose any name for the client to display
      "command": "uv",
      "args": [
        "run",
        "kibana-mcp"
      ],
      "options": {
          "cwd": "/path/to/kibana-mcp",
          "env": {
            // Ensure the server receives the required environment variables
            "KIBANA_URL": "<your_kibana_url>",
            "KIBANA_API_KEY": "<your_api_key_id>:<your_api_key_secret>"
          }
      }
    }
  }
}
```

*(Note: Storing secrets directly in the config file is generally discouraged for production use. Consider more secure ways to manage environment variables if needed.)*

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

### Debugging

Debugging MCP servers via stdio can be tricky. We recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

Launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) (replace `/path/to/kibana-mcp`):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/kibana-mcp run kibana-mcp
```

Access the URL provided by the Inspector in your browser.

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