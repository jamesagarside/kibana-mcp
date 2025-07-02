import httpx
from typing import List, Optional, Dict, Any
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_update_case(
    http_client: httpx.AsyncClient,
    case_id: str,
    version: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    assignees: Optional[List[Dict[str, str]]] = None,
    category: Optional[str] = None,
    connector_id: Optional[str] = None,
    connector_name: Optional[str] = None,
    connector_type: Optional[str] = None,
    connector_fields: Optional[Dict[str, Any]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    settings: Optional[Dict[str, bool]] = None
) -> str:
    """Handles the API interaction for updating a case."""
    api_path = "/api/cases"

    # Build the update payload - only include fields that are being updated
    case_update = {
        "id": case_id,
        "version": version
    }

    if title is not None:
        case_update["title"] = title
    if description is not None:
        case_update["description"] = description
    if tags is not None:
        case_update["tags"] = tags
    if assignees is not None:
        case_update["assignees"] = assignees
    if category is not None:
        case_update["category"] = category
    if severity is not None:
        case_update["severity"] = severity
    if status is not None:
        case_update["status"] = status
    if settings is not None:
        case_update["settings"] = settings
    if custom_fields is not None:
        case_update["customFields"] = custom_fields

    # Handle connector updates
    if any([connector_id, connector_name, connector_type, connector_fields]):
        case_update["connector"] = {}
        if connector_id is not None:
            case_update["connector"]["id"] = connector_id
        if connector_name is not None:
            case_update["connector"]["name"] = connector_name
        if connector_type is not None:
            case_update["connector"]["type"] = connector_type
        if connector_fields is not None:
            case_update["connector"]["fields"] = connector_fields

    payload = {"cases": [case_update]}

    result_text = f"Updating case {case_id} with version {version}"

    try:
        response = await http_client.patch(api_path, json=payload)
        response.raise_for_status()
        case_data = response.json()
        result_text = json.dumps(case_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
        result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        result_text += f"\nUnexpected error during case update: {str(e)}"

    return result_text
