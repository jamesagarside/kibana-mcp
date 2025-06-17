import httpx
from typing import List, Dict, Optional, Any
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_export_objects(
    http_client: httpx.AsyncClient,
    objects: List[Dict[str, Any]],
    exclude_export_details: Optional[bool] = None,
    include_references: Optional[bool] = None,
    include_namespace: Optional[bool] = None
) -> str:
    """Handles the API interaction for exporting saved objects."""
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

    # Build the API path
    api_path = "/api/saved_objects/_export"

    # Build query parameters
    params = {}
    if exclude_export_details is not None:
        params["exclude_export_details"] = str(exclude_export_details).lower()
    if include_references is not None:
        params["include_references"] = str(include_references).lower()
    if include_namespace is not None:
        params["include_namespace"] = str(include_namespace).lower()

    # Build request body
    request_body = {
        "objects": objects
    }

    tool_logger.info(f"Exporting {len(objects)} saved objects")

    try:
        # The export API may return NDJSON data rather than JSON
        response = await http_client.post(
            api_path,
            params=params,
            json=request_body
        )
        response.raise_for_status()

        # Handle NDJSON response - convert to JSON array
        content_type = response.headers.get('content-type', '')
        if 'application/ndjson' in content_type or 'application/x-ndjson' in content_type:
            # Parse NDJSON (one JSON object per line)
            result = []
            for line in response.text.strip().split('\n'):
                if line:
                    try:
                        result.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return json.dumps(result, indent=2)
        else:
            # Regular JSON response
            try:
                result = response.json()
                return json.dumps(result, indent=2)
            except json.JSONDecodeError:
                # If not valid JSON but successful HTTP response, return raw text
                return json.dumps({
                    "success": True,
                    "raw_response": response.text
                }, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"Error exporting saved objects: {str(e)}"
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
