import httpx
from typing import List, Optional, Dict, Callable, Awaitable
import mcp.types as types
import json # Added json import
import logging # Add logging import

# Setup logger for this module if not already present
tool_logger = logging.getLogger("kibana-mcp.tools")

# Note: We pass the http_client instance to the _call functions now

async def _call_tag_alert(http_client: httpx.AsyncClient, alert_id: str, tags_to_add: List[str]) -> str:
    """Handles the API interaction for tagging an alert signal."""
    # Correct endpoint for bulk actions on signals
    api_path = "/api/detection_engine/signals/bulk_actions"
    result_text = f"Attempting to add tags {tags_to_add} to alert signal {alert_id}..."

    # Construct the bulk action payload
    payload = {
        "signal_ids": [alert_id], # Target specific signal ID
        "action": "add_tags",   # Action to perform
        "tags": tags_to_add      # Tags to add
        # Note: No need to fetch existing tags; this endpoint likely appends.
        # Check docs if merging behavior is different.
    }

    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        # Check response content for success/failure details if available
        response_data = response.json()
        success_msg = response_data.get("message", "Update successful (check response details).")
        result_text += f"\nKibana API response: {response.status_code} - {success_msg}"

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except Exception as e:
         result_text = f"Error processing tag update for alert {alert_id}: {str(e)}"

    return result_text

async def _call_adjust_alert_status(http_client: httpx.AsyncClient, alert_id: str, new_status: str) -> str:
    """Handles the API interaction for adjusting alert signal status."""
    # Use the specific endpoint for setting signal status
    api_path = "/api/detection_engine/signals/status"
    
    # Validate status input slightly
    valid_statuses = ["open", "acknowledged", "closed"] # Add "in-progress" if needed
    if new_status not in valid_statuses:
        return f"Error: Invalid status '{new_status}'. Must be one of {valid_statuses}."

    result_text = f"Attempting to change status of alert signal {alert_id} to {new_status}..."

    # Construct the payload for the signals/status endpoint
    payload = {
        "signal_ids": [alert_id],
        "status": new_status
    }

    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        response_data = response.json()
        # Try to extract a meaningful success message, e.g., based on 'updated' count
        updated_count = response_data.get("updated", 0)
        if updated_count > 0:
            success_msg = f"Successfully updated status for {updated_count} signal(s)."
        else:
            success_msg = "Status update request processed, but no signals were updated (check ID or current status)."
        result_text += f"\nKibana API response: {response.status_code} - {success_msg}"

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except Exception as e:
         result_text += f"\nUnexpected error during status update: {str(e)}"

    return result_text

# Added new function implementation
async def _call_get_alerts(http_client: httpx.AsyncClient, limit: int = 20, search_text: Optional[str] = None) -> str:
    """Handles the API interaction for fetching alerts."""
    # Correct API endpoint for searching alert signals
    api_path = "/api/detection_engine/signals/search"
    
    # The payload structure might need adjustment for this endpoint.
    # Start with a basic query, check Kibana dev tools/docs for exact format.
    # Using a simple match_all query for now if no search_text provided.
    query: Dict = {"match_all": {}}
    if search_text:
        query = {
            "multi_match": {
                "query": search_text,
                "fields": ["kibana.alert.rule.name", "signal.rule.name", "message", "host.name", "user.name"] # Example fields, adjust as needed
            }
        }

    payload = {
        "query": query,
        "size": limit, # Elasticsearch uses 'size', not 'per_page'
        "sort": [
            {"@timestamp": {"order": "desc"}} # Sorting format for Elasticsearch
        ]
        # Removed fields unsupported by this endpoint like page, per_page, sort_field, search_fields, default_search_operator
    }

    result_text = f"Attempting to fetch up to {limit} alerts (signals)"
    if search_text:
        result_text += f" matching '{search_text}'"
    result_text += "..."

    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        alerts_data = response.json()
        result_text = json.dumps(alerts_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
         result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
         result_text += f"\nUnexpected error during alert signal fetch: {str(e)}"

    return result_text 

# Helper function to execute tools safely
async def execute_tool_safely(
    tool_name: str,
    tool_impl_func: Callable[..., Awaitable[str]], # Type hint for the _call_... funcs
    http_client: httpx.AsyncClient,
    **kwargs
) -> list[types.TextContent]:
    """Wraps tool execution with client check, logging, and error handling."""
    if not http_client:
        tool_logger.error(f"HTTP client not initialized when attempting to call tool '{tool_name}'.")
        raise RuntimeError("HTTP client not initialized.")
    
    tool_logger.info(f"Executing tool '{tool_name}' with args: {kwargs}")
    try:
        # Pass the client and other args to the specific implementation
        result_text = await tool_impl_func(http_client=http_client, **kwargs)
        tool_logger.info(f"Tool '{tool_name}' executed successfully.")
        return [types.TextContent(type="text", text=str(result_text))]
    except TypeError as e:
        # Catch argument mismatches specifically
        tool_logger.error(f"Invalid arguments passed to tool '{tool_name}' implementation: {e}", exc_info=True)
        # Raise a more specific error if possible, or a generic one
        raise ValueError(f"Invalid arguments provided for tool '{tool_name}': {e}")
    except Exception as e:
        tool_logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        raise RuntimeError(f"An error occurred while executing tool '{tool_name}'.") 