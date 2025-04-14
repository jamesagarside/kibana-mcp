import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

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