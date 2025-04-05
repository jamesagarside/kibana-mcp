import asyncio
import os
import httpx
import base64
from typing import List

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server, JSONSchema
import mcp.server.stdio

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

# Initialize MCP server
server = Server("kibana-mcp")

# Initialize httpx client (configured later)
http_client: httpx.AsyncClient | None = None

@server.initialize
def configure_client(options: InitializationOptions):
    """Configure the httpx client after initialization using env vars."""
    global http_client
    kibana_url = os.getenv("KIBANA_URL")
    api_key_id_secret = os.getenv("KIBANA_API_KEY") # Expecting "id:secret" format

    if not kibana_url:
        raise ValueError("KIBANA_URL environment variable not set.")
    if not api_key_id_secret:
        raise ValueError("KIBANA_API_KEY environment variable not set (expected 'id:secret' format).")

    # Encode API key for header
    encoded_api_key = base64.b64encode(api_key_id_secret.encode()).decode('ascii')

    headers = {
        "Authorization": f"ApiKey {encoded_api_key}",
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

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available note resources.
    Each note is exposed as a resource with a custom note:// URI scheme.
    """
    return [
        types.Resource(
            uri=AnyUrl(f"note://internal/{name}"),
            name=f"Note: {name}",
            description=f"A simple note named {name}",
            mimeType="text/plain",
        )
        for name in notes
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific note's content by its URI.
    The note name is extracted from the URI host component.
    """
    if uri.scheme != "note":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    name = uri.path
    if name is not None:
        name = name.lstrip("/")
        return notes[name]
    raise ValueError(f"Note not found: {name}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    The prompt includes all current notes and can be customized via arguments.
    """
    if name != "summarize-notes":
        raise ValueError(f"Unknown prompt: {name}")

    style = (arguments or {}).get("style", "brief")
    detail_prompt = " Give extensive details." if style == "detailed" else ""

    return types.GetPromptResult(
        description="Summarize the current notes",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
                    + "\n".join(
                        f"- {name}: {content}"
                        for name, content in notes.items()
                    ),
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available Kibana Security tools.
    """
    return [
        types.Tool(
            name="tag_alert",
            description="Adds one or more tags to a specific Kibana security alert.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": "The ID of the Kibana alert to tag."
                    },
                    "tags": {
                        "type": "array",
                        "description": "A list of tags to add to the alert.",
                        "items": {"type": "string"}
                    },
                },
                "required": ["alert_id", "tags"],
            },
        ),
        types.Tool(
            name="adjust_alert_severity",
            description="Changes the severity of a specific Kibana security alert.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": "The ID of the Kibana alert."
                    },
                    "new_severity": {
                        "type": "string",
                        "description": "The new severity level.",
                        "enum": ["informational", "low", "medium", "high", "critical"]
                    },
                },
                "required": ["alert_id", "new_severity"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Kibana alerts.
    """
    global http_client
    if not http_client:
        raise RuntimeError("HTTP client not initialized. KIBANA_URL and KIBANA_API_KEY must be set.")
    if not arguments:
        raise ValueError("Missing arguments")

    alert_id = arguments.get("alert_id")
    if not alert_id:
        raise ValueError("Missing required argument: alert_id")

    # Construct the API endpoint URL
    # NOTE: This endpoint might vary depending on Kibana version/config
    # It assumes alerts are managed by the 'alerting' plugin.
    # We might need to fetch the alert first to get its current state for updates.
    api_path = f"/api/alerting/alert/{alert_id}/_update"

    payload = {}
    result_text = ""

    if name == "tag_alert":
        tags_to_add = arguments.get("tags")
        if not tags_to_add or not isinstance(tags_to_add, list):
            raise ValueError("Missing or invalid required argument: tags (must be a list of strings)")

        # Kibana update API might require providing the full new state,
        # or it might support partial updates/scripts.
        # Assuming a simple script to append tags for now, adjust if needed.
        # This requires fetching the alert first to get existing tags.
        try:
            get_resp = await http_client.get(f"/api/alerting/alert/{alert_id}")
            get_resp.raise_for_status()
            current_alert = get_resp.json()
            existing_tags = current_alert.get("tags", [])
            # Avoid duplicate tags
            updated_tags = list(set(existing_tags + tags_to_add))

            payload = {"tags": updated_tags}
            result_text = f"Attempting to add tags {tags_to_add} to alert {alert_id}..."

        except httpx.HTTPStatusError as e:
            return [types.TextContent(type="text", text=f"Error fetching alert {alert_id} to update tags: {e.response.status_code} - {e.response.text}")]
        except Exception as e:
             return [types.TextContent(type="text", text=f"Error preparing tag update for alert {alert_id}: {str(e)}")]

    elif name == "adjust_alert_severity":
        new_severity = arguments.get("new_severity")
        if not new_severity:
            raise ValueError("Missing required argument: new_severity")

        # Assuming severity is stored within alert 'params'
        payload = {"params": {"severity": new_severity}} # Adjust path if severity is stored elsewhere
        result_text = f"Attempting to change severity of alert {alert_id} to {new_severity}..."

    else:
        raise ValueError(f"Unknown tool: {name}")

    # Make the update request
    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        result_text += f"\nKibana API response: {response.status_code} - Update successful."

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API: {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API returned error: {exc.response.status_code} - {exc.response.text}"

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