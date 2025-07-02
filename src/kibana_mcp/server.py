import asyncio
import os
import httpx
from typing import List, Optional, Dict, Any
import logging

# Import FastMCP and types
from fastmcp import FastMCP
import mcp.types as types

# Import handler implementations using absolute paths
from kibana_mcp.tools import (
    # Alert tools
    _call_tag_alert,
    _call_adjust_alert_status,
    _call_get_alerts,

    # Exception tools
    _call_get_rule_exceptions,
    _call_add_rule_exception_items,
    _call_create_exception_list,
    _call_associate_shared_exception_list,

    # Saved Objects tools
    _call_find_objects,
    _call_get_object,
    _call_bulk_get_objects,
    _call_create_object,
    _call_update_object,
    _call_delete_object,
    _call_export_objects,
    _call_import_objects,

    # Rule tools
    _call_find_rules,
    _call_get_rule,
    _call_delete_rule,
    _call_update_rule_status,
    _call_get_prepackaged_rules_status,
    _call_install_prepackaged_rules,

    # Endpoint tools
    _call_isolate_endpoint,
    _call_unisolate_endpoint,
    _call_run_command_on_endpoint,
    _call_get_response_actions,
    _call_get_response_action_details,
    _call_get_response_action_status,
    _call_kill_process,
    _call_suspend_process,
    _call_scan_endpoint,
    _call_get_file_info,
    _call_download_file,

    # Utils
    execute_tool_safely
)
from kibana_mcp.resources import handle_read_resource
from kibana_mcp.prompts import handle_get_prompt

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        auth_header = encoded_api_key if encoded_api_key.strip().startswith(
            "ApiKey ") else f"ApiKey {encoded_api_key.strip()}"
        headers["Authorization"] = auth_header
        auth_method_used = "API Key"
    elif kibana_username and kibana_password:
        logger.info(
            f"Configuring authentication using Basic auth for user: {kibana_username}")
        auth_config["auth"] = (kibana_username, kibana_password)
        auth_method_used = "Username/Password"
    else:
        logger.error("Kibana authentication not configured.")
        raise ValueError(
            "Kibana authentication not configured. Set KIBANA_API_KEY or both KIBANA_USERNAME/PASSWORD.")

    logger.info(
        f"Creating HTTP client for Kibana at {kibana_url} using {auth_method_used}.")
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
        tags_to_add=tags  # Pass correct arg name expected by _call_tag_alert
    )


@mcp.tool()
async def adjust_alert_status(alert_id: str, new_status: str) -> list[types.TextContent]:
    """Changes the status of a specific Kibana security alert signal."""
    # Basic validation remains here as it's specific to this tool's input
    valid_statuses = ["open", "acknowledged", "closed"]
    if new_status not in valid_statuses:
        err_msg = f"Invalid status '{new_status}'. Must be one of {valid_statuses}."
        logger.warning(
            f"Tool 'adjust_alert_status' called with invalid status for alert {alert_id}: {new_status}")
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

    The rule_id parameter should be the human-readable rule_id.
    The tool will automatically look up the internal UUID needed for the API call.

    Each exception item should follow this structure:
    {
      "name": "Sample Exception List Item",
      "tags": ["tag1", "tag2"],
      "type": "simple",
      "entries": [
        {
          "type": "exists",
          "field": "some.field.path",
          "operator": "included" or "excluded"
        },
        {
          "type": "match_any",
          "field": "another.field",
          "value": ["value1", "value2"],
          "operator": "included" or "excluded"
        }
      ],
      "description": "Description of this exception item",
      "namespace_type": "single" or "agnostic"
    }
    """
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

    The rule_id parameter should be the human-readable rule_id.
    The tool will automatically look up the internal UUID needed for the API call."""
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
    type: str,  # e.g., 'detection', 'endpoint'
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
    """Finds detection rules, optionally filtering by KQL/Lucene, sorting, and paginating.

    Args:
        filter: KQL or Lucene query string to filter rules. Field names must be prefixed with 
               'alert.attributes.' (e.g., 'alert.attributes.name:"Rule Name"' to filter by name).
               Example: 'alert.attributes.name:"Mock net10 alert"'
        sort_field: Field to sort by. Valid values are: 'created_at', 'createdAt', 'enabled', 
                   'execution_summary.last_execution.date', 
                   'execution_summary.last_execution.metrics.execution_gap_duration_s',
                   'execution_summary.last_execution.metrics.total_indexing_duration_ms', 
                   'execution_summary.last_execution.metrics.total_search_duration_ms',
                   'execution_summary.last_execution.status', 'name', 'risk_score', 
                   'riskScore', 'severity', 'updated_at', or 'updatedAt'.
        sort_order: Sort order. Valid values are 'asc' or 'desc'.
        page: Page number (minimum 1, default 1).
        per_page: Rules per page (minimum 0, default 20).
    """
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


@mcp.tool()
async def get_rule(
    rule_id: Optional[str] = None,
    id: Optional[str] = None
) -> list[types.TextContent]:
    """Retrieves details of a specific detection rule.

    Args:
        rule_id: The human-readable rule_id to fetch.
        id: The internal UUID of the rule to fetch.

    Note: You must provide either rule_id OR id parameter (not both).
    """
    return await execute_tool_safely(
        tool_name='get_rule',
        tool_impl_func=_call_get_rule,
        http_client=http_client,
        rule_id=rule_id,
        id=id
    )


@mcp.tool()
async def delete_rule(
    rule_id: Optional[str] = None,
    id: Optional[str] = None
) -> list[types.TextContent]:
    """Deletes a specific detection rule.

    Args:
        rule_id: The human-readable rule_id to delete.
        id: The internal UUID of the rule to delete.

    Note: You must provide either rule_id OR id parameter (not both).
    """
    return await execute_tool_safely(
        tool_name='delete_rule',
        tool_impl_func=_call_delete_rule,
        http_client=http_client,
        rule_id=rule_id,
        id=id
    )


@mcp.tool()
async def update_rule_status(
    rule_id: Optional[str] = None,
    id: Optional[str] = None,
    enabled: bool = True
) -> list[types.TextContent]:
    """Enables or disables a specific detection rule.

    Args:
        rule_id: The human-readable rule_id to update.
        id: The internal UUID of the rule to update.
        enabled: True to enable the rule, False to disable it (default: True).

    Note: You must provide either rule_id OR id parameter (not both).
    """
    return await execute_tool_safely(
        tool_name='update_rule_status',
        tool_impl_func=_call_update_rule_status,
        http_client=http_client,
        rule_id=rule_id,
        id=id,
        enabled=enabled
    )


@mcp.tool()
async def get_prepackaged_rules_status() -> list[types.TextContent]:
    """Retrieves the status of Elastic's prepackaged detection rules and timelines.

    Returns information about:
    - Number of custom rules installed
    - Number of prepackaged rules installed
    - Number of prepackaged rules available but not installed
    - Number of prepackaged rules that need updates
    - Timeline installation statistics
    """
    return await execute_tool_safely(
        tool_name='get_prepackaged_rules_status',
        tool_impl_func=_call_get_prepackaged_rules_status,
        http_client=http_client
    )


@mcp.tool()
async def install_prepackaged_rules() -> list[types.TextContent]:
    """Installs or updates Elastic's prepackaged detection rules and timelines.

    This tool:
    - Installs new prepackaged rules that aren't currently installed
    - Updates existing prepackaged rules that have been modified by Elastic
    - Installs new prepackaged timelines that aren't currently installed
    - Updates existing prepackaged timelines that have been modified by Elastic

    Returns a summary of installed and updated rules and timelines.
    """
    return await execute_tool_safely(
        tool_name='install_prepackaged_rules',
        tool_impl_func=_call_install_prepackaged_rules,
        http_client=http_client
    )

# --- Saved Objects Management Tools ---


@mcp.tool()
async def find_objects(
    type: List[str],
    search_fields: Optional[List[str]] = None,
    search: Optional[str] = None,
    default_search_operator: Optional[str] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = None,
    fields: Optional[List[str]] = None,
    filter: Optional[str] = None,
    has_reference: Optional[Dict[str, str]] = None
) -> list[types.TextContent]:
    """Find saved objects by type and other criteria.

    Note: Results are paginated by default (10 per page) to avoid exceeding conversation limits. 
    The total number of returned objects is limited to 100 to prevent excessive response lengths.
    Use the page parameter to navigate through results when working with large result sets.

    Args:
        type: A list of saved object types to search for.
        search_fields: A list of fields to search within.
        search: A search term to match against the search_fields.
        default_search_operator: Either 'AND' or 'OR' for how to combine search terms. Default is 'OR'.
        page: The page number to return. Defaults to 1.
        per_page: The number of objects to return per page. Defaults to 10.
        sort_field: The field to sort on.
        sort_order: Either 'asc' or 'desc' for the sort direction.
        fields: A list of fields to return in the response.
        filter: A KQL expression to filter on.
        has_reference: Filter by reference fields and values.
    """
    return await execute_tool_safely(
        tool_name='find_objects',
        tool_impl_func=_call_find_objects,
        http_client=http_client,
        type=type,
        search_fields=search_fields,
        search=search,
        default_search_operator=default_search_operator,
        page=page,
        per_page=per_page,
        sort_field=sort_field,
        sort_order=sort_order,
        fields=fields,
        filter=filter,
        has_reference=has_reference
    )


@mcp.tool()
async def get_object(
    type: str,
    id: str,
    include_references: Optional[bool] = None,
    fields: Optional[List[str]] = None
) -> list[types.TextContent]:
    """Get a saved object by type and ID.

    Args:
        type: The type of saved object to retrieve.
        id: The ID of the saved object.
        include_references: Whether to include references in the response.
        fields: A list of fields to return in the response.
    """
    return await execute_tool_safely(
        tool_name='get_object',
        tool_impl_func=_call_get_object,
        http_client=http_client,
        type=type,
        id=id,
        include_references=include_references,
        fields=fields
    )


@mcp.tool()
async def bulk_get_objects(
    objects: List[Dict[str, str]],
    include_references: Optional[bool] = None,
    fields: Optional[List[str]] = None
) -> list[types.TextContent]:
    """Get multiple saved objects in a single request.

    Args:
        objects: A list of objects with 'type' and 'id' properties.
        include_references: Whether to include references in the response.
        fields: A list of fields to return in the response.
    """
    return await execute_tool_safely(
        tool_name='bulk_get_objects',
        tool_impl_func=_call_bulk_get_objects,
        http_client=http_client,
        objects=objects,
        include_references=include_references,
        fields=fields
    )


@mcp.tool()
async def create_object(
    type: str,
    attributes: Dict[str, Any],
    id: Optional[str] = None,
    overwrite: Optional[bool] = None,
    references: Optional[list] = None
) -> list[types.TextContent]:
    """Create a new saved object.

    Args:
        type: The type of saved object to create.
        attributes: The attributes of the saved object.
        id: Optional ID to assign to the saved object. If not provided, one will be generated.
        overwrite: Whether to overwrite an existing object with the same ID.
        references: A list of references to other saved objects.
    """
    return await execute_tool_safely(
        tool_name='create_object',
        tool_impl_func=_call_create_object,
        http_client=http_client,
        type=type,
        attributes=attributes,
        id=id,
        overwrite=overwrite,
        references=references
    )


@mcp.tool()
async def update_object(
    type: str,
    id: str,
    attributes: Dict[str, Any],
    version: Optional[str] = None,
    references: Optional[list] = None
) -> list[types.TextContent]:
    """Update an existing saved object.

    Args:
        type: The type of saved object to update.
        id: The ID of the saved object.
        attributes: The attributes to update.
        version: The version of the saved object to update (for optimistic concurrency control).
        references: A list of references to other saved objects.
    """
    return await execute_tool_safely(
        tool_name='update_object',
        tool_impl_func=_call_update_object,
        http_client=http_client,
        type=type,
        id=id,
        attributes=attributes,
        version=version,
        references=references
    )


@mcp.tool()
async def delete_object(
    type: str,
    id: str,
    force: Optional[bool] = None
) -> list[types.TextContent]:
    """Delete a saved object.

    Args:
        type: The type of saved object to delete.
        id: The ID of the saved object.
        force: Whether to force deletion of the object even if it would break references.
    """
    return await execute_tool_safely(
        tool_name='delete_object',
        tool_impl_func=_call_delete_object,
        http_client=http_client,
        type=type,
        id=id,
        force=force
    )


@mcp.tool()
async def export_objects(
    objects: List[Dict[str, Any]],
    exclude_export_details: Optional[bool] = None,
    include_references: Optional[bool] = None,
    include_namespace: Optional[bool] = None
) -> list[types.TextContent]:
    """Export saved objects.

    Args:
        objects: A list of objects with 'type' and 'id' properties to export.
        exclude_export_details: Whether to exclude export details from the response.
        include_references: Whether to include referenced objects in the export.
        include_namespace: Whether to include the namespace in the exported objects.
    """
    return await execute_tool_safely(
        tool_name='export_objects',
        tool_impl_func=_call_export_objects,
        http_client=http_client,
        objects=objects,
        exclude_export_details=exclude_export_details,
        include_references=include_references,
        include_namespace=include_namespace
    )


@mcp.tool()
async def import_objects(
    objects_ndjson: str,
    create_new_copies: Optional[bool] = None,
    overwrite: Optional[bool] = None
) -> list[types.TextContent]:
    """Import saved objects.

    Args:
        objects_ndjson: A string containing the objects in NDJSON format.
        create_new_copies: Whether to create new copies of the objects with new IDs.
        overwrite: Whether to overwrite existing objects with the same ID.
    """
    return await execute_tool_safely(
        tool_name='import_objects',
        tool_impl_func=_call_import_objects,
        http_client=http_client,
        objects_ndjson=objects_ndjson,
        create_new_copies=create_new_copies,
        overwrite=overwrite
    )


# --- Endpoint Management Tools ---


@mcp.tool()
async def isolate_endpoint(
    endpoint_ids: List[str],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> list[types.TextContent]:
    """Isolate one or more endpoints from the network."""
    return await execute_tool_safely(
        tool_name='isolate_endpoint',
        tool_impl_func=_call_isolate_endpoint,
        http_client=http_client,
        endpoint_ids=endpoint_ids,
        agent_type=agent_type,
        comment=comment
    )


@mcp.tool()
async def unisolate_endpoint(
    endpoint_ids: List[str],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> list[types.TextContent]:
    """Release one or more endpoints from isolation."""
    return await execute_tool_safely(
        tool_name='unisolate_endpoint',
        tool_impl_func=_call_unisolate_endpoint,
        http_client=http_client,
        endpoint_ids=endpoint_ids,
        agent_type=agent_type,
        comment=comment
    )


@mcp.tool()
async def run_command_on_endpoint(
    endpoint_ids: List[str],
    command: str,
    agent_type: str = "endpoint",
    comment: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> list[types.TextContent]:
    """Run a shell command on one or more endpoints."""
    return await execute_tool_safely(
        tool_name='run_command_on_endpoint',
        tool_impl_func=_call_run_command_on_endpoint,
        http_client=http_client,
        endpoint_ids=endpoint_ids,
        command=command,
        agent_type=agent_type,
        comment=comment,
        parameters=parameters
    )


@mcp.tool()
async def get_response_actions(
    page: int = 1,
    page_size: int = 10,
    agent_ids: Optional[List[str]] = None,
    agent_types: Optional[str] = None,
    commands: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_ids: Optional[List[str]] = None,
    with_outputs: Optional[List[str]] = None
) -> list[types.TextContent]:
    """Get a list of all response actions from Elastic Defend endpoints."""
    return await execute_tool_safely(
        tool_name='get_response_actions',
        tool_impl_func=_call_get_response_actions,
        http_client=http_client,
        page=page,
        page_size=page_size,
        agent_ids=agent_ids,
        agent_types=agent_types,
        commands=commands,
        types=types,
        start_date=start_date,
        end_date=end_date,
        user_ids=user_ids,
        with_outputs=with_outputs
    )


@mcp.tool()
async def get_response_action_details(
    action_id: str
) -> list[types.TextContent]:
    """Get details of a response action by action ID."""
    return await execute_tool_safely(
        tool_name='get_response_action_details',
        tool_impl_func=_call_get_response_action_details,
        http_client=http_client,
        action_id=action_id
    )


@mcp.tool()
async def get_response_action_status(
    query: Dict[str, Any]
) -> list[types.TextContent]:
    """Get the status of response actions for specified agent IDs."""
    return await execute_tool_safely(
        tool_name='get_response_action_status',
        tool_impl_func=_call_get_response_action_status,
        http_client=http_client,
        query=query
    )


@mcp.tool()
async def kill_process(
    endpoint_ids: List[str],
    parameters: Dict[str, Any],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> list[types.TextContent]:
    """Terminate a running process on an endpoint."""
    return await execute_tool_safely(
        tool_name='kill_process',
        tool_impl_func=_call_kill_process,
        http_client=http_client,
        endpoint_ids=endpoint_ids,
        parameters=parameters,
        agent_type=agent_type,
        comment=comment
    )


@mcp.tool()
async def suspend_process(
    endpoint_ids: List[str],
    parameters: Dict[str, Any],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> list[types.TextContent]:
    """Suspend a running process on an endpoint."""
    return await execute_tool_safely(
        tool_name='suspend_process',
        tool_impl_func=_call_suspend_process,
        http_client=http_client,
        endpoint_ids=endpoint_ids,
        parameters=parameters,
        agent_type=agent_type,
        comment=comment
    )


@mcp.tool()
async def scan_endpoint(
    endpoint_ids: List[str],
    parameters: Dict[str, Any],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> list[types.TextContent]:
    """Scan a file or directory on an endpoint for malware."""
    return await execute_tool_safely(
        tool_name='scan_endpoint',
        tool_impl_func=_call_scan_endpoint,
        http_client=http_client,
        endpoint_ids=endpoint_ids,
        parameters=parameters,
        agent_type=agent_type,
        comment=comment
    )


@mcp.tool()
async def get_file_info(
    action_id: str,
    file_id: str
) -> list[types.TextContent]:
    """Get information for a file retrieved by a response action."""
    return await execute_tool_safely(
        tool_name='get_file_info',
        tool_impl_func=_call_get_file_info,
        http_client=http_client,
        action_id=action_id,
        file_id=file_id
    )


@mcp.tool()
async def download_file(
    action_id: str,
    file_id: str
) -> list[types.TextContent]:
    """Download a file from an endpoint."""
    return await execute_tool_safely(
        tool_name='download_file',
        tool_impl_func=_call_download_file,
        http_client=http_client,
        action_id=action_id,
        file_id=file_id
    )


def run_server():
    """Configure client, run the MCP server loop, and handle cleanup."""
    global http_client  # Need global to ensure cleanup happens
    http_client = None  # Ensure it's None initially

    # Check for SSE mode configuration
    transport_mode = os.getenv("MCP_TRANSPORT", "stdio").lower()

    try:
        configure_http_client()  # Configure global client

        if transport_mode == "sse":
            # SSE mode configuration
            host = os.getenv("MCP_SSE_HOST", "127.0.0.1")
            port = int(os.getenv("MCP_SSE_PORT", "8000"))

            logger.info(
                f"Starting FastMCP server in SSE mode on {host}:{port}...")
            logger.info(
                f"SSE endpoint will be available at: http://{host}:{port}/sse/")

            # Run SSE mode with new API
            mcp.run(transport="sse", host=host, port=port)
        else:
            # Default STDIO mode
            logger.info(f"Starting FastMCP server in STDIO mode...")
            mcp.run(transport="stdio")

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
                logger.error(
                    f"Error closing HTTP client in finally block: {re}", exc_info=True)
        else:
            logger.info("HTTP client was not initialized or already closed.")


# Allows running the server directly using `python -m kibana_mcp` or `uv run kibana-mcp`
if __name__ == "__main__":
    run_server()  # Call the synchronous function directly
