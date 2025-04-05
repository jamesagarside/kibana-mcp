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