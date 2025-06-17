import httpx
from typing import Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_delete_object(
    http_client: httpx.AsyncClient,
    type: str,
    id: str,
    force: Optional[bool] = None
) -> str:
    """Handles the API interaction for deleting a saved object."""
    if not type or not id:
        return json.dumps({
            "error": "Both 'type' and 'id' parameters are required."
        })

    # Build the API path
    api_path = f"/api/saved_objects/{type}/{id}"

    # Build query parameters
    params = {}
    if force is not None:
        params["force"] = str(force).lower()

    tool_logger.info(f"Deleting saved object of type '{type}' with ID '{id}'")

    try:
        response = await http_client.delete(
            api_path,
            params=params
        )
        response.raise_for_status()

        # Check if response is empty (204 No Content)
        if response.status_code == 204 or not response.content:
            return json.dumps({
                "success": True,
                "message": f"Successfully deleted saved object of type '{type}' with ID '{id}'"
            }, indent=2)

        result = response.json()
        return json.dumps(result, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"Error deleting saved object: {str(e)}"
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
