import httpx
from typing import Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_rule(
    http_client: httpx.AsyncClient,
    rule_id: Optional[str] = None,
    id: Optional[str] = None
) -> str:
    """Handles the API interaction for fetching a specific detection rule."""
    # Must provide either rule_id or id
    if not rule_id and not id:
        return "Error: You must provide either rule_id or id parameter."

    # Build the query parameters
    params = {}
    if rule_id:
        params["rule_id"] = rule_id
        result_text = f"Attempting to fetch rule with rule_id '{rule_id}'..."
    else:
        params["id"] = id
        result_text = f"Attempting to fetch rule with id '{id}'..."

    api_path = "/api/detection_engine/rules"

    try:
        # Get rule details
        response = await http_client.get(api_path, params=params)
        response.raise_for_status()

        # Process the response
        response_data = response.json()

        # Format the result in a user-friendly way
        formatted_result = {
            "id": response_data.get("id"),
            "rule_id": response_data.get("rule_id"),
            "name": response_data.get("name"),
            "description": response_data.get("description"),
            "risk_score": response_data.get("risk_score"),
            "severity": response_data.get("severity"),
            "type": response_data.get("type"),
            "enabled": response_data.get("enabled", False),
            "created_at": response_data.get("created_at"),
            "updated_at": response_data.get("updated_at"),
            "tags": response_data.get("tags", []),
            "interval": response_data.get("interval"),
            "from": response_data.get("from"),
            "to": response_data.get("to")
        }

        # Add query details if present
        if "query" in response_data:
            formatted_result["query"] = response_data["query"]

        # Add execution summary if present
        if "execution_summary" in response_data:
            formatted_result["execution_summary"] = response_data["execution_summary"]

        # Return a nicely formatted JSON string of the result
        return f"Rule fetched successfully:\n\n{json.dumps(formatted_result, indent=2)}"

    except httpx.RequestError as exc:
        return f"Error connecting to Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        error_text = f"Kibana API ({api_path}) returned error: {exc.response.status_code}"
        try:
            error_data = exc.response.json()
            if "message" in error_data:
                error_text += f" - {error_data['message']}"
            else:
                error_text += f" - {exc.response.text}"
        except:
            error_text += f" - {exc.response.text}"
        return error_text
    except json.JSONDecodeError:
        return f"Error parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        return f"Unexpected error getting rule details: {str(e)}"
