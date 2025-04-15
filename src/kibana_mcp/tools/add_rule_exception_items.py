import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_add_rule_exception_items(http_client: httpx.AsyncClient, rule_id: str, items: List[Dict]) -> str:
    """Handles the API interaction for adding exception items to a rule's list."""
    # Endpoint from the provided documentation
    # IMPORTANT: rule_id must be the internal UUID (id) of the rule, not the user-facing rule_id
    api_path = f"/api/detection_engine/rules/{rule_id}/exceptions"
    result_text = f"Attempting to add {len(items)} exception item(s) to rule {rule_id}..."
    
    # The payload structure requires the items under an "items" key
    # IMPORTANT: Based on trial-and-error, list_id should be omitted from the item dict
    # when using this endpoint, as the list is implied by the rule association.
    items_without_list_id = []
    for item in items:
        new_item = item.copy()
        if 'list_id' in new_item:
            del new_item['list_id'] 
        items_without_list_id.append(new_item)

    payload = {"items": items_without_list_id}

    try:
        # Add the Elastic-Api-Version header as specified in the docs for POST
        headers = {"Elastic-Api-Version": "2023-10-31"}
        response = await http_client.post(api_path, json=payload, headers=headers)
        response.raise_for_status()
        # Response contains the created items with their IDs
        response_data = response.json()
        result_text += f"\\nSuccessfully added items. Response:\\n{json.dumps(response_data, indent=2)}"

    except httpx.RequestError as exc:
        result_text += f"\\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
         result_text += f"\\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
         result_text += f"\\nUnexpected error adding rule exception items: {str(e)}"
         
    return result_text
