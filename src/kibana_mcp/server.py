import asyncio
import os
import httpx
import base64
from typing import List

# Ensure correct import path if models was moved
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server, JSONSchema
import mcp.server.stdio
# Assuming pydantic might be needed by resources/prompts if they use AnyUrl etc.
from pydantic import AnyUrl

# Import tool handlers
from .tools import handle_list_tools, _call_tag_alert, _call_adjust_alert_severity
# Import new resource handlers
from .resources import handle_list_resources, handle_read_resource
# Import new prompt handlers
from .prompts import handle_list_prompts, handle_get_prompt

# Initialize MCP server
server = Server("kibana-mcp")

# Initialize httpx client (configured later)
http_client: httpx.AsyncClient | None = None

@server.initialize
def configure_client(options: InitializationOptions):
    """Configure the httpx client after initialization using env vars."""
    global http_client
    kibana_url = os.getenv("KIBANA_URL")
    # Expecting the value to be already Base64 encoded "id:secret"
    encoded_api_key = os.getenv("KIBANA_API_KEY") 

    if not kibana_url:
        raise ValueError("KIBANA_URL environment variable not set.")
    if not encoded_api_key:
        raise ValueError("KIBANA_API_KEY environment variable not set (expected Base64 encoded 'id:secret').")

    headers = {
        "Authorization": f"ApiKey {encoded_api_key}", # Use the env var directly
        "kbn-xsrf": "true", # Kibana requires this header
        "Content-Type": "application/json"
    }
    http_client = httpx.AsyncClient(base_url=kibana_url, headers=headers, timeout=30.0)

@server.shutdown
async def close_client():
    """Close the httpx client on shutdown."""
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None

# Register resource handlers
server.list_resources()(handle_list_resources)
server.read_resource()(handle_read_resource)

# Register prompt handlers
server.list_prompts()(handle_list_prompts)
server.get_prompt()(handle_get_prompt)

# Register tool handlers
server.list_tools()(handle_list_tools)

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Kibana alerts by dispatching to specific handlers.
    """
    global http_client
    if not http_client:
        raise RuntimeError("HTTP client not initialized. KIBANA_URL and KIBANA_API_KEY must be set.")
    if not arguments:
        raise ValueError("Missing arguments")

    alert_id = arguments.get("alert_id")
    if not alert_id or not isinstance(alert_id, str):
        raise ValueError("Missing or invalid required argument: alert_id (must be a string)")

    result_text = ""

    if name == "tag_alert":
        tags_to_add = arguments.get("tags")
        if not tags_to_add or not isinstance(tags_to_add, list) or not all(isinstance(tag, str) for tag in tags_to_add):
            raise ValueError("Missing or invalid required argument: tags (must be a list of strings)")
        result_text = await _call_tag_alert(http_client, alert_id, tags_to_add)

    elif name == "adjust_alert_severity":
        new_severity = arguments.get("new_severity")
        # Optional: Add validation against the enum defined in the schema if desired, though MCP client should handle this
        if not new_severity or not isinstance(new_severity, str):
            raise ValueError("Missing or invalid required argument: new_severity (must be a string)")
        result_text = await _call_adjust_alert_severity(http_client, alert_id, new_severity)

    else:
        raise ValueError(f"Unknown tool: {name}")

    return [types.TextContent(type="text", text=result_text)]

async def main():
    """Main entry point to run the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kibana-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    # No notifications needed for these tools
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )

# Allows running the server directly using `python -m kibana_mcp` or `uv run kibana-mcp`
if __name__ == "__main__":
    asyncio.run(main())