import httpx
from typing import List
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_delete_cases(http_client: httpx.AsyncClient, case_ids: List[str]) -> str:
    """Handles the API interaction for deleting cases."""
    api_path = "/api/cases"

    # Build query parameters
    params = {"ids": case_ids}

    result_text = f"Deleting cases with IDs: {case_ids}"

    try:
        response = await http_client.delete(api_path, params=params)
        response.raise_for_status()

        # Successful deletion returns 204 No Content
        if response.status_code == 204:
            result_text = f"Successfully deleted {len(case_ids)} case(s): {case_ids}"
        else:
            result_text = f"Unexpected response status: {response.status_code}"

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except Exception as e:
        result_text += f"\nUnexpected error during case deletion: {str(e)}"

    return result_text
