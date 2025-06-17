import httpx
from typing import Dict, Any, Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_create_object(
    http_client: httpx.AsyncClient,
    type: str,
    attributes: Dict[str, Any],
    id: Optional[str] = None,
    overwrite: Optional[bool] = None,
    references: Optional[list] = None
) -> str:
    """Handles the API interaction for creating a saved object."""
    if not type:
        return json.dumps({
            "error": "The 'type' parameter is required."
        })

    if not attributes or not isinstance(attributes, dict):
        return json.dumps({
            "error": "The 'attributes' parameter is required and must be a dictionary."
        })

    # Build the API path
    api_path = f"/api/saved_objects/{type}"
    if id:
        api_path = f"{api_path}/{id}"

    # Build query parameters
    params = {}
    if overwrite is not None:
        params["overwrite"] = str(overwrite).lower()

    # Build request body
    request_body = {
        "attributes": attributes
    }
    if references:
        request_body["references"] = references

    tool_logger.info(
        f"Creating saved object of type '{type}'{' with ID ' + id if id else ''}")

    try:
        response = await http_client.post(
            api_path,
            params=params,
            json=request_body
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"Error creating saved object: {str(e)}"
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
