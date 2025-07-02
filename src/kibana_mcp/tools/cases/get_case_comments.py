import httpx
from typing import List, Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_case_comments(
    http_client: httpx.AsyncClient,
    case_id: str,
    page: int = 1,
    per_page: int = 20,
    sort_order: str = "desc"
) -> str:
    """Handles the API interaction for getting case comments."""
    api_path = f"/api/cases/{case_id}/comments/_find"

    # Build query parameters
    params = {
        "page": page,
        "perPage": per_page,
        "sortOrder": sort_order
    }

    result_text = f"Fetching comments for case {case_id}"

    try:
        response = await http_client.get(api_path, params=params)
        response.raise_for_status()
        comments_data = response.json()
        result_text = json.dumps(comments_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
        result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        result_text += f"\nUnexpected error during comment retrieval: {str(e)}"

    return result_text
