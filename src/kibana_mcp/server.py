import asyncio
import os
import httpx
import base64
from typing import List, Optional, Dict, Callable, Awaitable

# Ensure correct import path if models was moved
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
# Assuming pydantic might be needed by resources/prompts if they use AnyUrl etc.
from pydantic import AnyUrl

# Import tool handlers
from .tools import handle_list_tools, _call_tag_alert, _call_adjust_alert_severity, _call_get_alerts
# Import new resource handlers
from .resources import handle_list_resources, handle_read_resource
# Import new prompt handlers
from .prompts import handle_list_prompts, handle_get_prompt

# Initialize MCP server
server = Server("kibana-mcp")

# Initialize httpx client (configured later)
http_client: httpx.AsyncClient | None = None

# --- Tool Function Mapping ---
# Define a type hint for async tool functions
ToolFunction = Callable[[httpx.AsyncClient, Dict], Awaitable[str]]

TOOL_FUNCTION_MAP: Dict[str, ToolFunction] = {
    "tag_alert": _call_tag_alert,
    "adjust_alert_severity": _call_adjust_alert_severity,
    "get_alerts": _call_get_alerts,
}
# --- End Tool Function Mapping ---

# Remove the decorator, we will call this function manually
# @server.initialize
def configure_client(): # Remove options parameter
    """
    Configure the httpx client after initialization using env vars.
    Supports API Key (KIBANA_API_KEY) or Username/Password (KIBANA_USERNAME, KIBANA_PASSWORD).
    API Key is prioritized if both are provided.
    """
    global http_client
    kibana_url = os.getenv("KIBANA_URL")
    # Expecting the API key value to be already Base64 encoded "id:secret"
    encoded_api_key = os.getenv("KIBANA_API_KEY")
    kibana_username = os.getenv("KIBANA_USERNAME")
    kibana_password = os.getenv("KIBANA_PASSWORD")

    if not kibana_url:
        raise ValueError("KIBANA_URL environment variable not set.")

    headers = {
        "kbn-xsrf": "true", # Kibana requires this header
        "Content-Type": "application/json"
    }
    auth_config = {}
    auth_method_used = "None"

    # Prioritize API Key
    if encoded_api_key:
        print("Using API Key authentication.")
        # Prepend "ApiKey " if it's not already there (common mistake)
        auth_header = encoded_api_key if encoded_api_key.strip().startswith("ApiKey ") else f"ApiKey {encoded_api_key.strip()}"
        headers["Authorization"] = auth_header
        auth_method_used = "API Key"
    elif kibana_username and kibana_password:
        print(f"Using Basic authentication for user: {kibana_username}")
        auth_config["auth"] = (kibana_username, kibana_password)
        auth_method_used = "Username/Password"
    else:
        raise ValueError("Kibana authentication not configured. Set either KIBANA_API_KEY or both KIBANA_USERNAME and KIBANA_PASSWORD environment variables.")

    print(f"Configuring HTTP client for Kibana at {kibana_url} using {auth_method_used}.")
    # Consider making verify configurable via env var as well for non-local environments
    http_client = httpx.AsyncClient(
        base_url=kibana_url,
        headers=headers,
        timeout=30.0,
        verify=False, # Added verify=False for local testing ease, set True for production
        **auth_config
    )

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
    Handle tool execution requests by dispatching to the correct function based on the tool name.
    """
    global http_client
    if not http_client:
        # This should technically not happen if initialization succeeded
        raise RuntimeError("HTTP client not initialized. Ensure Kibana connection details are correctly set in environment variables.")
    if not arguments:
        # Allow tools that might not need arguments, let the specific tool function validate
        arguments = {} # Provide an empty dict if None

    if name in TOOL_FUNCTION_MAP:
        try:
            # Pass the http_client and the arguments dictionary to the specific tool function
            result_text = await TOOL_FUNCTION_MAP[name](http_client=http_client, **arguments)
        except TypeError as e:
            # Catch errors if arguments don't match the function signature (e.g., missing required args)
            raise ValueError(f"Invalid arguments provided for tool '{name}': {e}")
        except Exception as e:
            # Catch other potential errors from the tool function itself
            # Log the full error for debugging if possible
            print(f"Error executing tool '{name}': {e}")
            raise RuntimeError(f"An error occurred while executing tool '{name}'.")
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [types.TextContent(type="text", text=str(result_text))] # Ensure result is string

async def main():
    """Main entry point to run the server."""
    # Configure the client before starting the server run loop
    configure_client()

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