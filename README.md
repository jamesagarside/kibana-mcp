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
*   `KIBANA_API_KEY`: Your Kibana API key in the format `id:secret`. Generate this in Kibana under Stack Management -> API Keys. Ensure the key has permissions to read and update alerts (e.g., appropriate privileges for the Alerting plugin).

## Quickstart

### Running the Server

Ensure you have set the required environment variables (`KIBANA_URL`, `KIBANA_API_KEY`). Then, navigate to the project directory and run the server using `uv`:

```bash
cd kibana-mcp
export KIBANA_URL="<your_kibana_url>"
export KIBANA_API_KEY="<your_api_key_id>:<your_api_key_secret>"
uv run kibana-mcp
```

The server will start and listen for MCP connections via standard input/output.

### Connecting a Client (e.g., Claude Desktop)

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
          // Ensure the command runs within the correct project directory
          "cwd": "/path/to/kibana-mcp",
           // Pass required environment variables if not set globally
          "env": {
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

Since MCP servers run over stdio, debugging can be challenging. For the best debugging experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command (replace `/path/to/kibana-mcp` with the actual project path):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/kibana-mcp run kibana-mcp
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

## Local Development & Testing

To test this server locally, you can use the provided Docker Compose configuration to spin up local Elasticsearch and Kibana instances.

**Prerequisites:**

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

**Steps:**

1.  **Check Passwords:**
    *   Open the `docker-compose.yml` file.
    *   The default password for the `elastic` user is set to `elastic` for both the `elasticsearch` and `kibana` services. You can change this if needed, but ensure it's the same in both places and update the healthcheck command if you do.
    *   **Warning:** Do not use the default password in a production environment.
    *   *(Optional but recommended)*: If you want Elasticsearch data to persist across container restarts, uncomment the `volumes` section at the bottom of `docker-compose.yml` and the `volumes` line under the `elasticsearch` service definition.

2.  **Start Services:**
    *   Open your terminal in the root directory of this repository.
    *   Run the command:
        ```bash
        docker-compose up -d
        ```
    *   This command will download the necessary Docker images (if not already present) and start the Elasticsearch and Kibana containers in the background. Healthchecks are included to ensure Kibana waits for Elasticsearch to be ready.

3.  **Access Services:**
    *   **Elasticsearch:** Available at `http://localhost:9200`
    *   **Kibana:** Available at `http://localhost:5601`
    *   Login to Kibana using the username `elastic` and the password set in `docker-compose.yml` (default is `elastic`).

4.  **Configure MCP Server:**
    *   When running the Kibana MCP server (e.g., `main.py`), configure it to connect to the local Kibana instance:
        *   Set the Kibana base URL to `http://localhost:5601`.
        *   Use the username `elastic` and the password `elastic` (or the one you set).

5.  **Testing:**
    *   You can now send requests to your MCP server, which will interact with the local Kibana instance.
    *   You might need to manually create some sample alerts or data within Kibana via its UI (`http://localhost:5601`) to test the `get_alerts`, `tag_alert`, and `adjust_alert_severity` tools effectively.

6.  **Stop Services:**
    *   When you're finished testing, stop the containers:
        ```bash
        docker-compose down
        ```
    *   If you configured persistent volumes and want to remove the Elasticsearch data volume, add the `-v` flag:
        ```bash
        docker-compose down -v
        ```

## Running the Server

(Add instructions here on how to install dependencies and run the main server script, e.g., `main.py`)

```bash
# Example:
pip install -r requirements.txt
python src/kibana_mcp/main.py --kibana-url <your_kibana_url> --username <user> --password <pass>
```

## Available Tools

*   `tag_alert`: Adds tags to a Kibana security alert.
*   `adjust_alert_severity`: Changes the severity of a Kibana security alert.
*   `get_alerts`: Fetches recent Kibana security alerts.