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
    # Correct endpoint based on Kibana v8 documentation for adding/removing tags
    api_path = "/api/detection_engine/signals/tags"
    result_text = f"Attempting to add tags {tags_to_add} to alert signal {alert_id}..."

    # Construct the payload required by the /signals/tags endpoint
    payload = {
        "ids": [alert_id], # Target specific signal ID (using 'ids' key)
        "tags": {          # Nested 'tags' object
            "tags_to_add": tags_to_add,
            "tags_to_remove": [] # Explicitly sending empty list for removal
        }
    }

    try:
        # The API docs mention Elastic-Api-Version header, but let's try without first
        # If issues persist, consider adding: headers={"Elastic-Api-Version": "2023-10-31"}
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        # Process the response which might be an Elasticsearch update-by-query response
        response_data = response.json()
        # Extract meaningful info if possible, e.g., 'updated' count
        updated_count = response_data.get('updated', 'N/A')
        result_text += f"\nKibana API response: {response.status_code} - Updated: {updated_count}"

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
async def _call_get_alerts(http_client: httpx.AsyncClient, limit: int, search_text: str) -> str:
    """Handles the API interaction for fetching alerts using Elasticsearch query DSL."""
    # Correct API endpoint for searching alert signals
    api_path = "/api/detection_engine/signals/search"

    # Construct the base Elasticsearch bool query
    bool_query: Dict = {
        "bool": {
            "must": [],
            "filter": [],
            "should": [],
            "must_not": []
        }
    }

    # If search_text is provided AND is not the default '*', add it as a multi_match filter
    if search_text != "*":
        # Place the multi_match query inside the 'filter' context for non-scoring search
        bool_query["bool"]["filter"].append({
            "multi_match": {
                "query": search_text,
                "fields": [
                    "kibana.alert.rule.name",
                    "kibana.alert.reason", # Added reason field
                    "signal.rule.name",    # Kept signal.rule.name just in case
                    "message",             # Kept message
                    "host.name",           # Kept host.name
                    "user.name",           # Kept user.name
                    "kibana.alert.rule.description", # Added description
                    "kibana.alert.uuid",   # Allow searching by alert UUID
                    "_id"                  # Allow searching by internal _id
                    # Add more fields as needed
                ]
            }
        })
    # If no search text, the bool query with empty clauses acts like match_all

    payload = {
        "query": bool_query, # Use the constructed bool query
        "size": limit,
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ]
        # Add other potential payload fields like aggregations, _source filtering etc. if needed
    }

    result_text = f"Attempting to fetch up to {limit} alerts (signals)"
    if search_text != "*":
        result_text += f" matching '{search_text}' using bool query"
    else:
        result_text += f" (matching all, as search_text is default '*')"
    result_text += "..."

    try:
        # Consider adding headers={"Elastic-Api-Version": "2023-10-31"} if needed
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