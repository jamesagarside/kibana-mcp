import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_create_exception_list(
    http_client: httpx.AsyncClient,
    list_id: str, 
    name: str,
    description: str,
    type: str, # e.g., 'detection', 'endpoint'
    namespace_type: str = 'single', # 'single' or 'agnostic'
    tags: Optional[List[str]] = None,
    os_types: Optional[List[str]] = None # 'linux', 'macos', 'windows'
) -> str:
    """Handles the API interaction for creating an exception list container."""
    api_path = "/api/exception_lists"
    result_text = f"Attempting to create exception list with list_id '{list_id}'..."

    # Construct payload, handling optional fields
    payload = {
        "list_id": list_id,
        "name": name,
        "description": description,
        "type": type,
        "namespace_type": namespace_type,
    }
    if tags is not None:
        payload["tags"] = tags
    if os_types is not None:
        payload["os_types"] = os_types # API expects an array

    try:
        # Add the Elastic-Api-Version header as specified in the docs
        headers = {"Elastic-Api-Version": "2023-10-31"}
        response = await http_client.post(api_path, json=payload, headers=headers)
        
        # Handle 409 Conflict specifically - list_id might already exist
        if response.status_code == 409:
            result_text += f"\\nKibana API ({api_path}) returned 409 Conflict: An exception list with list_id '{list_id}' may already exist."
            # Optionally, you could try to fetch the existing list here
            # result_text += f"\\nResponse: {response.text}" # Include response body for debugging
            return result_text # Return the specific conflict message
        
        response.raise_for_status() # Raise for other errors (4xx, 5xx)
        
        # Response contains the created list details
        response_data = response.json()
        created_id = response_data.get('id', 'N/A') # Get the Kibana internal ID
        result_text += f"\\nSuccessfully created exception list. Internal ID: {created_id}"
        result_text += f"\\nResponse:\\n{json.dumps(response_data, indent=2)}"

    except httpx.RequestError as exc:
        result_text += f"\\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        # Log other HTTP errors (excluding the 409 handled above)
        result_text += f"\\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
         result_text += f"\\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
         result_text += f"\\nUnexpected error creating exception list: {str(e)}"
         
    return result_text 