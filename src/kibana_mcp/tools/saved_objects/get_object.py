import httpx
from typing import Optional, List
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_object(
    http_client: httpx.AsyncClient,
    type: str,
    id: str,
    include_references: Optional[bool] = None,
    fields: Optional[List[str]] = None
) -> str:
    """Handles the API interaction for retrieving a single saved object by ID."""
    if not type or not id:
        return json.dumps({
            "error": "Both 'type' and 'id' parameters are required."
        })

    # Build the API path for getting a specific object
    api_path = f"/api/saved_objects/{type}/{id}"

    # Build query parameters
    params = {}
    if include_references is not None:
        params["include_references"] = str(include_references).lower()
    if fields:
        params["fields"] = ",".join(fields)

    tool_logger.info(f"Getting saved object of type '{type}' with ID '{id}'")

    try:
        response = await http_client.get(
            api_path,
            params=params
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"Error retrieving saved object: {str(e)}"
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

            if status_code == 404:
                error_msg = f"Saved object of type '{type}' with ID '{id}' not found"

        tool_logger.error(error_msg)
        return json.dumps({
            "error": error_msg
        })
