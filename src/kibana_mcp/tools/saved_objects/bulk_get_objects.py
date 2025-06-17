import httpx
from typing import List, Dict, Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_bulk_get_objects(
    http_client: httpx.AsyncClient,
    objects: List[Dict[str, str]],
    include_references: Optional[bool] = None,
    fields: Optional[List[str]] = None
) -> str:
    """Handles the API interaction for retrieving multiple saved objects by ID in bulk."""
    if not objects or not isinstance(objects, list):
        return json.dumps({
            "error": "The 'objects' parameter is required and must be a list of objects with 'type' and 'id' properties."
        })

    # Check if all objects have required fields
    for obj in objects:
        if not isinstance(obj, dict) or 'type' not in obj or 'id' not in obj:
            return json.dumps({
                "error": "Each object must have 'type' and 'id' properties."
            })

    # Build the API path for bulk get
    api_path = "/api/saved_objects/_bulk_get"

    # Build query parameters
    params = {}
    if include_references is not None:
        params["include_references"] = str(include_references).lower()
    if fields:
        params["fields"] = ",".join(fields)

    tool_logger.info(f"Retrieving {len(objects)} saved objects in bulk")

    try:
        response = await http_client.post(
            api_path,
            params=params,
            json={"objects": objects}
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"Error retrieving saved objects in bulk: {str(e)}"
        if hasattr(e, "response") and getattr(e, "response") is not None:
            status_code = e.response.status_code
            if e.response.text:
                try:
                    error_details = e.response.json()
                    error_msg = f"HTTP {status_code}: {json.dumps(error_details)}"
                except json.JSONDecodeError:
                    error_msg = f"HTTP {status_code}: {e.response.text}"
            else:
                error_msg = f"HTTP {status_code}: {str(e)}"

        tool_logger.error(error_msg)
        return json.dumps({
            "error": error_msg
        })
