import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_find_cases(
    http_client: httpx.AsyncClient,
    assignees: Optional[List[str]] = None,
    category: Optional[str] = None,
    default_search_operator: str = "OR",
    from_date: Optional[str] = None,
    owner: Optional[List[str]] = None,
    page: int = 1,
    per_page: int = 20,
    reporters: Optional[List[str]] = None,
    search: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    severity: Optional[str] = None,
    sort_field: str = "created_at",
    sort_order: str = "desc",
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    to_date: Optional[str] = None
) -> str:
    """Handles the API interaction for searching cases."""
    api_path = "/api/cases/_find"

    # Build query parameters
    params = {
        "page": page,
        "perPage": per_page,
        "sortField": sort_field,
        "sortOrder": sort_order,
        "defaultSearchOperator": default_search_operator
    }

    # Add optional parameters
    if assignees:
        params["assignees"] = assignees
    if category:
        params["category"] = category
    if from_date:
        params["from"] = from_date
    if owner:
        params["owner"] = owner
    if reporters:
        params["reporters"] = reporters
    if search:
        params["search"] = search
    if search_fields:
        params["searchFields"] = search_fields
    if severity:
        params["severity"] = severity
    if status:
        params["status"] = status
    if tags:
        params["tags"] = tags
    if to_date:
        params["to"] = to_date

    result_text = f"Searching for cases with parameters: {params}"

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
        result_text += f"\nUnexpected error during case search: {str(e)}"

    return result_text
