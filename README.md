# Kibana MCP Server

Model Context Protocol (MCP) server for Kibana Security functions - manage alerts, rules, and exceptions via AI assistants.

## Quick Start

### 1. Set Environment Variables
```bash
export KIBANA_URL="https://your-kibana.example.com:5601"
export KIBANA_API_KEY="your_base64_api_key"
# OR use username/password:
# export KIBANA_USERNAME="username"
# export KIBANA_PASSWORD="password"
```

### 2. Run with Docker
```bash
docker build -t kibana-mcp .
docker run -i --rm -e KIBANA_URL -e KIBANA_API_KEY kibana-mcp
```

### 3. Add to MCP Client
Add to your MCP client config (Claude Desktop, Cursor, etc.):
```json
{
  "mcpServers": {
    "kibana-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "KIBANA_URL", "-e", "KIBANA_API_KEY", "kibana-mcp"]
    }
  }
}
```

## Available Tools

- **`get_alerts`** - Fetch security alerts
- **`tag_alert`** - Add tags to alerts  
- **`adjust_alert_status`** - Change alert status (open/acknowledged/closed)
- **`find_rules`** - Search detection rules
- **`get_rule_exceptions`** - Get rule exception items
- **`add_rule_exception_items`** - Add exceptions to rules
- **`create_exception_list`** - Create new exception lists
- **`associate_shared_exception_list`** - Link exception lists to rules

## Local Development

```bash
# Install dependencies
uv sync

# Set environment variables (see above)

# Run locally
uv run kibana-mcp
```

### Test Environment
```bash
# Start local Kibana/Elasticsearch with test data
pip install -r requirements-dev.txt
./testing/quickstart-test-env.sh

# Access at http://localhost:5601 (elastic/elastic)
```

## Configuration

**MCP Client Locations:**
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Cursor: `~/.cursor/mcp.json`

**Authentication:**
- API Key (recommended): Generate in Kibana → Stack Management → API Keys
- Username/Password: Basic auth credentials