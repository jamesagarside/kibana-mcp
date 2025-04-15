import httpx
from typing import List, Optional, Dict
import json
import logging
from pydantic import ValidationError

from kibana_mcp.models.rule_models import FindRulesRequest

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_find_rules(
    http_client: httpx.AsyncClient,
    filter: Optional[str] = None,      # KQL or Lucene query string (e.g., 'alert.attributes.name:"Rule Name"')
    sort_field: Optional[str] = None,  # Field to sort by (e.g., 'name', 'updated_at')
    sort_order: Optional[str] = None,  # 'asc' or 'desc'
    page: Optional[int] = None,        # Page number (1-based)
    per_page: Optional[int] = None     # Items per page (default typically 20)
) -> str:
    """Handles the API interaction for finding detection rules."""
    # Validate input using Pydantic model
    try:
        # Create the request model
        request = FindRulesRequest(
            filter=filter,
            sort_field=sort_field,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        # Validation passed
        result_text = f"Validated and attempting to find rules"
    except ValidationError as e:
        return f"Input validation error: {str(e)}"
    
    api_path = "/api/detection_engine/rules/_find"

    # Construct query parameters from validated request
    params = {}
    if request.filter:
        params["filter"] = request.filter
        result_text += f" with filter '{request.filter}'"
    if request.sort_field:
        params["sort_field"] = request.sort_field.value  # Get the string value from the enum
    if request.sort_order:
        params["sort_order"] = request.sort_order.value  # Get the string value from the enum
    if request.page:
        params["page"] = request.page
    if request.per_page:
        params["per_page"] = request.per_page
    
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
