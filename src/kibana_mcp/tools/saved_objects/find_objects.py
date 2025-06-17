import httpx
from typing import Optional, Dict, Any, List
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

# Default values to limit response size
DEFAULT_PER_PAGE = 10
DEFAULT_MAX_RESULTS = 100


async def _call_find_objects(
    http_client: httpx.AsyncClient,
    type: List[str],
    search_fields: Optional[List[str]] = None,
    search: Optional[str] = None,
    default_search_operator: Optional[str] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = None,
    fields: Optional[List[str]] = None,
    filter: Optional[str] = None,
    has_reference: Optional[Dict[str, str]] = None
) -> str:
    """Handles the API interaction for finding saved objects based on various criteria."""
    api_path = "/api/saved_objects/_find"

    # Build query parameters
    params = {}

    # Required parameter
    if type:
        params["type"] = ",".join(type)
    else:
        return json.dumps({
            "error": "The 'type' parameter is required."
        })

    # Optional parameters
    if search_fields:
        params["search_fields"] = ",".join(search_fields)
    if search:
        params["search"] = search
    if default_search_operator:
        params["default_search_operator"] = default_search_operator
    # Always use pagination to limit response size
    params["page"] = page if page is not None else 1
    params["per_page"] = per_page if per_page is not None else DEFAULT_PER_PAGE
    if sort_field:
        params["sort_field"] = sort_field
    if sort_order:
        params["sort_order"] = sort_order
    if fields:
        params["fields"] = ",".join(fields)
    if filter:
        params["filter"] = filter

    # Handle has_reference parameter, which has a special structure
    if has_reference:
        for key, value in has_reference.items():
            params[f"has_reference[{key}]"] = value

    tool_logger.info(
        f"Finding saved objects of type: {type} with search: {search}"
    )

    try:
        response = await http_client.get(
            api_path,
            params=params
        )
        response.raise_for_status()
        result = response.json()

        # Format the response for better readability
        total = result.get("total", 0)
        current_page = result.get("page", 0)
        objects_per_page = result.get("per_page", 0)
        saved_objects = result.get("saved_objects", [])

        # Truncate results if necessary to avoid hitting conversation limits
        original_count = len(saved_objects)
        if len(saved_objects) > DEFAULT_MAX_RESULTS:
            saved_objects = saved_objects[:DEFAULT_MAX_RESULTS]

        formatted_result = {
            "total": total,
            "per_page": objects_per_page,
            "page": current_page,
            "saved_objects": saved_objects
        }

        # Add warnings if results were truncated or if there are more pages
        warnings = []
        if original_count > DEFAULT_MAX_RESULTS:
            warnings.append(
                f"Results truncated: showing {DEFAULT_MAX_RESULTS} of {original_count} objects to avoid exceeding conversation limits.")

        if total > current_page * objects_per_page:
            remaining_pages = (
                total - 1) // objects_per_page + 1 - current_page
            if remaining_pages > 0:
                warnings.append(f"Found {total} total objects across {remaining_pages + current_page} pages. " +
                                f"Currently showing page {current_page} of {objects_per_page} objects per page. " +
                                "Use 'page' parameter to view other pages.")

        if warnings:
            formatted_result["warnings"] = warnings

        return json.dumps(formatted_result, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"Error finding saved objects: {str(e)}"
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
