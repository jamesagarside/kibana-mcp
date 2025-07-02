import httpx
from typing import List, Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_cases_by_alert(
    http_client: httpx.AsyncClient,
    alert_id: str,
    owner: Optional[List[str]] = None
) -> str:
    """Handles the API interaction for getting cases that contain a specific alert."""
    api_path = f"/api/cases/alerts/{alert_id}"

    # Build query parameters
    params = {}
    if owner:
        params["owner"] = owner

    result_text = f"Fetching cases containing alert {alert_id}"

    try:
        response = await http_client.get(api_path, params=params)
        response.raise_for_status()
        cases_data = response.json()
        result_text = json.dumps(cases_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
        result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        result_text += f"\nUnexpected error during case retrieval: {str(e)}"

    return result_text
