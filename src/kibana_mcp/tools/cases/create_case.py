import httpx
from typing import List, Optional, Dict, Any
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_create_case(
    http_client: httpx.AsyncClient,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    assignees: Optional[List[Dict[str, str]]] = None,
    category: Optional[str] = None,
    connector_id: str = "none",
    connector_name: str = "none",
    connector_type: str = ".none",
    connector_fields: Optional[Dict[str, Any]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None,
    owner: str = "securitySolution",
    severity: str = "low",
    settings: Optional[Dict[str, bool]] = None
) -> str:
    """Handles the API interaction for creating a new case."""
    api_path = "/api/cases"

    # Build the case payload
    payload = {
        "title": title,
        "description": description,
        "tags": tags or [],
        "connector": {
            "id": connector_id,
            "name": connector_name,
            "type": connector_type,
            "fields": connector_fields or None
        },
        "owner": owner,
        "severity": severity
    }

    # Add optional fields
    if assignees:
        payload["assignees"] = assignees
    if category:
        payload["category"] = category
    if custom_fields:
        payload["customFields"] = custom_fields
    if settings:
        payload["settings"] = settings

    result_text = f"Creating case with title: '{title}'"

    try:
        response = await http_client.post(api_path, json=payload)
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
        result_text += f"\nUnexpected error during case creation: {str(e)}"

    return result_text
