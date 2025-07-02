import httpx
from typing import List, Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_case_tags(
    http_client: httpx.AsyncClient,
    owner: Optional[List[str]] = None
) -> str:
    """Handles the API interaction for getting all case tags."""
    api_path = "/api/cases/tags"

    # Build query parameters
    params = {}
    if owner:
        params["owner"] = owner

    result_text = "Fetching case tags"

    try:
        response = await http_client.get(api_path, params=params)
        response.raise_for_status()
        tags_data = response.json()
        result_text = json.dumps(tags_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
        result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        result_text += f"\nUnexpected error during tags retrieval: {str(e)}"

    return result_text
