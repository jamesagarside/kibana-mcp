import asyncio
import os
import httpx
from typing import List, Optional, Dict
import logging

# Import FastMCP and types
from fastmcp import FastMCP
import mcp.types as types

# Import handler implementations using absolute paths
from kibana_mcp.tools import (
    _call_tag_alert, 
    _call_adjust_alert_status, 
    _call_get_alerts, 
    _call_get_rule_exceptions, 
    _call_add_rule_exception_items, 
    _call_create_exception_list,
    _call_associate_shared_exception_list,
    _call_find_rules,
    execute_tool_safely
)
from kibana_mcp.resources import handle_read_resource
from kibana_mcp.prompts import handle_get_prompt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kibana-mcp")

# --- Global MCP Instance and HTTP Client ---
logger.info("Initializing Kibana MCP Server (FastMCP)...")
mcp = FastMCP("kibana-mcp")
http_client: httpx.AsyncClient | None = None

def configure_http_client():
    """Configure the global httpx client using environment variables."""
    global http_client
    kibana_url = os.getenv("KIBANA_URL")
    encoded_api_key = os.getenv("KIBANA_API_KEY")
    kibana_username = os.getenv("KIBANA_USERNAME")
    kibana_password = os.getenv("KIBANA_PASSWORD")
    kibana_space = os.getenv("KIBANA_SPACE")

    if not kibana_url:
        logger.error("KIBANA_URL environment variable not set.")
        raise ValueError("KIBANA_URL environment variable not set.")
    
    # Modify the base URL to include the space if specified
    if kibana_space:
        # Remove trailing slash if present
        if kibana_url.endswith('/'):
            kibana_url = kibana_url[:-1]
        # Add the space to the URL
        kibana_url = f"{kibana_url}/s/{kibana_space}"
        logger.info(f"Using Kibana space: {kibana_space}")

    headers = {"kbn-xsrf": "true", "Content-Type": "application/json"}
    auth_config = {}
    auth_method_used = "None"

    if encoded_api_key:
        logger.info("Configuring authentication using API Key.")
        auth_header = encoded_api_key if encoded_api_key.strip().startswith("ApiKey ") else f"ApiKey {encoded_api_key.strip()}"
        headers["Authorization"] = auth_header
        auth_method_used = "API Key"
    elif kibana_username and kibana_password:
        logger.info(f"Configuring authentication using Basic auth for user: {kibana_username}")
        auth_config["auth"] = (kibana_username, kibana_password)
        auth_method_used = "Username/Password"
    else:
        logger.error("Kibana authentication not configured.")
        raise ValueError("Kibana authentication not configured. Set KIBANA_API_KEY or both KIBANA_USERNAME/PASSWORD.")

    logger.info(f"Creating HTTP client for Kibana at {kibana_url} using {auth_method_used}.")
    http_client = httpx.AsyncClient(
        base_url=kibana_url, headers=headers, timeout=30.0, verify=False, **auth_config
    )

async def close_http_client():
    """Close the global httpx client."""
    global http_client
    if http_client:
        logger.info("Closing HTTP client...")
        await http_client.aclose()
        http_client = None
        logger.info("HTTP client closed.")

# --- Handler Functions with FastMCP Decorators ---

# NOTE: list_* handlers might need specific registration if not automatic

@mcp.resource("alert://{alert_id}")
async def read_alert_resource(alert_id: str) -> str:
    uri = f"alert://{alert_id}"
    logger.info(f"Handling read_resource for URI: {uri}")
    return await handle_read_resource(uri=uri)

@mcp.prompt("prompt://{prompt_name}")
async def get_kibana_prompt(prompt_name: str) -> types.GetPromptResult:
    uri = f"prompt://{prompt_name}"
    logger.info(f"Handling get_prompt for URI: {uri}")
    return await handle_get_prompt(uri=uri)

# --- Individual Tool Handlers ---

@mcp.tool()
async def tag_alert(alert_id: str, tags: List[str]) -> list[types.TextContent]:
    """Adds one or more tags to a specific Kibana security alert signal."""
    # Delegate execution to the safe wrapper
    return await execute_tool_safely(
        tool_name='tag_alert',
        tool_impl_func=_call_tag_alert,
        http_client=http_client,
        alert_id=alert_id, 
        tags_to_add=tags # Pass correct arg name expected by _call_tag_alert
    )

@mcp.tool()
async def adjust_alert_status(alert_id: str, new_status: str) -> list[types.TextContent]:
    """Changes the status of a specific Kibana security alert signal."""
    # Basic validation remains here as it's specific to this tool's input
    valid_statuses = ["open", "acknowledged", "closed"]
    if new_status not in valid_statuses:
         err_msg = f"Invalid status '{new_status}'. Must be one of {valid_statuses}."
         logger.warning(f"Tool 'adjust_alert_status' called with invalid status for alert {alert_id}: {new_status}")
         return [types.TextContent(type="text", text=err_msg)]

    # Delegate execution to the safe wrapper
    return await execute_tool_safely(
        tool_name='adjust_alert_status',
        tool_impl_func=_call_adjust_alert_status,
        http_client=http_client,
        alert_id=alert_id, 
        new_status=new_status
    )

@mcp.tool()
async def get_alerts(limit: int = 20, 
                     search_text: str = "*"
                     ) -> list[types.TextContent]:
    """Fetches recent Kibana security alert signals, optionally filtering by text and limiting quantity."""
    # Delegate execution to the safe wrapper, extracting values from the args model
    return await execute_tool_safely(
        tool_name='get_alerts',
        tool_impl_func=_call_get_alerts,
        http_client=http_client,
        limit=limit, 
        search_text=search_text
    )

@mcp.tool()
async def add_rule_exception_items(rule_id: str, items: List[Dict]) -> list[types.TextContent]:
    """Adds one or more exception items to a specific detection rule's exception list.
    
    Note: The rule_id parameter must be the Kibana internal UUID (id) of the rule, 
    not the user-facing rule_id. You can get the internal UUID by using the find_rules tool."""
    # Delegate execution to the safe wrapper
    return await execute_tool_safely(
        tool_name='add_rule_exception_items',
        tool_impl_func=_call_add_rule_exception_items,
        http_client=http_client,
        rule_id=rule_id,
        items=items
    )

@mcp.tool()
async def get_rule_exceptions(rule_id: str) -> list[types.TextContent]:
    """Retrieves the exception items associated with a specific detection rule.
    
    Note: The rule_id parameter must be the Kibana internal UUID (id) of the rule, 
    not the user-facing rule_id. You can get the internal UUID by using the find_rules tool."""
    # Delegate execution to the safe wrapper
    return await execute_tool_safely(
        tool_name='get_rule_exceptions',
        tool_impl_func=_call_get_rule_exceptions,
        http_client=http_client,
        rule_id=rule_id
    )

@mcp.tool()
async def create_exception_list(
    list_id: str,
    name: str,
    description: str,
    type: str, # e.g., 'detection', 'endpoint'
    namespace_type: str = 'single',
    tags: Optional[List[str]] = None,
    os_types: Optional[List[str]] = None
) -> list[types.TextContent]:
    """Creates a new exception list container.

    Args:
        list_id: Human-readable identifier for the list (e.g., 'trusted-ips').
        name: Display name for the exception list.
        description: Description of the list's purpose.
        type: Type of list ('detection', 'endpoint', etc.).
        namespace_type: Scope ('single' or 'agnostic', default: 'single').
        tags: Optional list of tags.
        os_types: Optional list of OS types ('linux', 'macos', 'windows').
    """
    # Delegate execution to the safe wrapper
    return await execute_tool_safely(
        tool_name='create_exception_list',
        tool_impl_func=_call_create_exception_list,
        http_client=http_client,
        list_id=list_id,
        name=name,
        description=description,
        type=type,
        namespace_type=namespace_type,
        tags=tags,
        os_types=os_types
    )

@mcp.tool()
async def associate_shared_exception_list(
    rule_id: str,
    exception_list_id: str,
    exception_list_type: str = 'detection',
    exception_list_namespace: str = 'single'
) -> list[types.TextContent]:
    """Associates an existing shared exception list (not a rule default) with a detection rule."""
    # Delegate execution to the safe wrapper
    return await execute_tool_safely(
        tool_name='associate_shared_exception_list',
        tool_impl_func=_call_associate_shared_exception_list,
        http_client=http_client,
        rule_id=rule_id,
        exception_list_id=exception_list_id,
        exception_list_type=exception_list_type,
        exception_list_namespace=exception_list_namespace
    )

@mcp.tool()
async def find_rules(
    filter: Optional[str] = None,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> list[types.TextContent]:
    """Finds detection rules, optionally filtering by KQL/Lucene, sorting, and paginating."""
    return await execute_tool_safely(
        tool_name='find_rules',
        tool_impl_func=_call_find_rules,
        http_client=http_client,
        filter=filter,
        sort_field=sort_field,
        sort_order=sort_order,
        page=page,
        per_page=per_page
    )

def run_server():
    """Configure client, run the MCP server loop, and handle cleanup."""
    global http_client # Need global to ensure cleanup happens
    http_client = None # Ensure it's None initially
    try:
        configure_http_client() # Configure global client
        logger.info(f"Starting FastMCP server run loop...")
        # Call the synchronous run method, which handles the event loop
        mcp.run()
        logger.info(f"FastMCP server run loop finished normally.")
    except Exception as e:
        logger.error(f"Error during server run: {e}", exc_info=True)
    finally:
        logger.info("Shutting down server...")
        # Need to run the async close in a temporary event loop
        if http_client:
            try:
                # Create a new loop *just* for closing the client if run finished/errored
                asyncio.run(close_http_client())
            except RuntimeError as re:
                # Handle case where loop might already be closed or another issue
                logger.error(f"Error closing HTTP client in finally block: {re}", exc_info=True)
        else:
             logger.info("HTTP client was not initialized or already closed.")

# Allows running the server directly using `python -m kibana_mcp` or `uv run kibana-mcp`
if __name__ == "__main__":
    run_server() # Call the synchronous function directly
