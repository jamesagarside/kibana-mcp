import httpx
from typing import List, Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_case_alerts(http_client: httpx.AsyncClient, case_id: str) -> str:
    """Handles the API interaction for getting alerts attached to a case."""
    api_path = f"/api/cases/{case_id}/alerts"

    result_text = f"Fetching alerts for case {case_id}"

    try:
        response = await http_client.get(api_path)
        response.raise_for_status()
        alerts_data = response.json()
        result_text = json.dumps(alerts_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
        result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        result_text += f"\nUnexpected error during alert retrieval: {str(e)}"

    return result_text
