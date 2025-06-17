import httpx
from typing import Optional, List
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_import_objects(
    http_client: httpx.AsyncClient,
    objects_ndjson: str,
    create_new_copies: Optional[bool] = None,
    overwrite: Optional[bool] = None
) -> str:
    """Handles the API interaction for importing saved objects."""
    if not objects_ndjson:
        return json.dumps({
            "error": "The 'objects_ndjson' parameter is required."
        })

    # Build the API path
    api_path = "/api/saved_objects/_import"

    # Build query parameters
    params = {}
    if create_new_copies is not None:
        params["createNewCopies"] = str(create_new_copies).lower()
    if overwrite is not None:
        params["overwrite"] = str(overwrite).lower()

    # Create form data with file
    import io
    files = {
        'file': ('import.ndjson', io.StringIO(objects_ndjson), 'application/ndjson')
    }

    tool_logger.info(f"Importing saved objects")

    try:
        response = await http_client.post(
            api_path,
            params=params,
            files=files
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"Error importing saved objects: {str(e)}"
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
