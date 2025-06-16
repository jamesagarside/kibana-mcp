import httpx
from typing import Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_delete_rule(
    http_client: httpx.AsyncClient,
    rule_id: Optional[str] = None,
    id: Optional[str] = None
) -> str:
    """Handles the API interaction for deleting a detection rule."""
    # Must provide either rule_id or id
    if not rule_id and not id:
        return "Error: You must provide either rule_id or id parameter."

    # Build the query parameters
    params = {}
    if rule_id:
        params["rule_id"] = rule_id
        result_text = f"Attempting to delete rule with rule_id '{rule_id}'..."
    else:
        params["id"] = id
        result_text = f"Attempting to delete rule with id '{id}'..."

    api_path = "/api/detection_engine/rules"

    try:
        # Send the delete request
        response = await http_client.delete(api_path, params=params)
        response.raise_for_status()

        # Process the response
        response_data = response.json()

        # Extract key information about the deleted rule
        rule_name = response_data.get("name", "Unknown rule")
        rule_id_value = response_data.get("rule_id", "Unknown rule_id")

        return f"Successfully deleted rule '{rule_name}' (rule_id: {rule_id_value})"

    except httpx.RequestError as exc:
        return f"{result_text}\nError connecting to Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        error_text = f"{result_text}\nKibana API ({api_path}) returned error: {exc.response.status_code}"
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
        return f"{result_text}\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        return f"{result_text}\nUnexpected error deleting rule: {str(e)}"
