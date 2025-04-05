import httpx
from typing import List, Optional
import mcp.types as types
import json # Added json import

# Note: We pass the http_client instance to the _call functions now

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
        ),
        types.Tool( # Added new tool definition
            name="get_alerts",
            description="Fetches recent Kibana security alerts, optionally filtered by text and limited in quantity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of alerts to return (default: 20).",
                        "default": 20
                    },
                    "search_text": {
                        "type": "string",
                        "description": "Text to search for in alert fields (optional)."
                    },
                    # Add other potential filters like status, severity, time range later if needed
                },
                "required": [], # No required parameters for basic fetch
            },
        )
    ]

async def _call_tag_alert(http_client: httpx.AsyncClient, alert_id: str, tags_to_add: List[str]) -> str:
    """Handles the API interaction for tagging an alert."""
    # Removed global check as client is passed in
    api_path_get = f"/api/alerting/alert/{alert_id}"
    api_path_update = f"/api/alerting/alert/{alert_id}/_update"
    result_text = f"Attempting to add tags {tags_to_add} to alert {alert_id}..."

    try:
        # Fetch the current alert to get existing tags
        get_resp = await http_client.get(api_path_get)
        get_resp.raise_for_status()
        current_alert = get_resp.json()
        existing_tags = current_alert.get("tags", [])

        # Avoid duplicate tags
        updated_tags = list(set(existing_tags + tags_to_add))
        payload = {"tags": updated_tags}

        # Make the update request
        response = await http_client.post(api_path_update, json=payload)
        response.raise_for_status()
        result_text += f"\nKibana API response: {response.status_code} - Update successful."

    except httpx.HTTPStatusError as e:
        if e.request.method == 'GET':
             result_text = f"Error fetching alert {alert_id} to update tags: {e.response.status_code} - {e.response.text}"
        else:
             result_text += f"\nKibana API returned error during update: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API: {exc}"
    except Exception as e:
         # Catch potential JSON parsing errors or other issues
         result_text = f"Error processing tag update for alert {alert_id}: {str(e)}"

    return result_text

async def _call_adjust_alert_severity(http_client: httpx.AsyncClient, alert_id: str, new_severity: str) -> str:
    """Handles the API interaction for adjusting alert severity."""
    # Removed global check as client is passed in
    api_path = f"/api/alerting/alert/{alert_id}/_update"
    # Assuming severity is stored within alert 'params'
    payload = {"params": {"severity": new_severity}} # Adjust path if severity is stored elsewhere
    result_text = f"Attempting to change severity of alert {alert_id} to {new_severity}..."

    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        result_text += f"\nKibana API response: {response.status_code} - Update successful."

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API: {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API returned error: {exc.response.status_code} - {exc.response.text}"
    except Exception as e:
         result_text += f"\nUnexpected error during severity update: {str(e)}"

    return result_text

# Added new function implementation
async def _call_get_alerts(http_client: httpx.AsyncClient, limit: int = 20, search_text: Optional[str] = None) -> str:
    """Handles the API interaction for fetching alerts."""
    api_path = "/api/alerting/alerts/_find"
    # Default sorting by start time, newest first
    payload = {
        "page": 1,
        "per_page": limit,
        "sort_field": "start",
        "sort_order": "desc",
        "search_fields": ["alert.name", "kibana.alert.rule.name"], # Fields to search within if search_text is provided
        "default_search_operator": "AND"
    }
    if search_text:
        payload["search"] = search_text

    result_text = f"Attempting to fetch up to {limit} alerts"
    if search_text:
        result_text += f" matching '{search_text}'"
    result_text += "..."

    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        alerts_data = response.json()
        # Return a JSON string representation of the fetched alerts
        result_text = json.dumps(alerts_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"
Error calling Kibana API: {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"
Kibana API returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
         result_text += f"
Error parsing JSON response from Kibana API."
    except Exception as e:
         result_text += f"
Unexpected error during alert fetch: {str(e)}"

    return result_text 