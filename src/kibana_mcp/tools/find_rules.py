import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_find_rules(
    http_client: httpx.AsyncClient,
    filter: Optional[str] = None,      # KQL or Lucene query string
    sort_field: Optional[str] = None,  # Field to sort by (e.g., 'name', 'updated_at')
    sort_order: Optional[str] = None,  # 'asc' or 'desc'
    page: Optional[int] = None,        # Page number (1-based)
    per_page: Optional[int] = None     # Items per page (default typically 20)
) -> str:
    """Handles the API interaction for finding detection rules."""
    api_path = "/api/detection_engine/rules/_find"
    result_text = f"Attempting to find rules"

    # Construct query parameters
    params = {}
    if filter:
        params["filter"] = filter
        result_text += f" with filter '{filter}'"
    if sort_field:
        params["sort_field"] = sort_field
    if sort_order:
        params["sort_order"] = sort_order
    if page:
        params["page"] = page
    if per_page:
        params["per_page"] = per_page
    
    result_text += "..."

    try:
        response = await http_client.get(api_path, params=params)
        response.raise_for_status()
        response_data = response.json()
        result_text = json.dumps(response_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
         result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
         result_text += f"\nUnexpected error finding rules: {str(e)}"
         
    return result_text 