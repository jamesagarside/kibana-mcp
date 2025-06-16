import httpx
from typing import Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_update_rule_status(
    http_client: httpx.AsyncClient,
    rule_id: Optional[str] = None,
    id: Optional[str] = None,
    enabled: bool = True
) -> str:
    """Handles the API interaction for enabling or disabling a detection rule."""
    # Must provide either rule_id or id
    if not rule_id and not id:
        return "Error: You must provide either rule_id or id parameter."

    # Build the query parameters for the GET request
    params = {}
    if rule_id:
        params["rule_id"] = rule_id
        identifier_text = f"rule_id '{rule_id}'"
    else:
        params["id"] = id
        identifier_text = f"id '{id}'"

    action = "enable" if enabled else "disable"
    result_text = f"Attempting to {action} rule with {identifier_text}..."
    api_path = "/api/detection_engine/rules"

    try:
        # First, we need to get the current rule to preserve all its fields
        get_response = await http_client.get(api_path, params=params)
        get_response.raise_for_status()

        # Get the current rule data
        rule_data = get_response.json()

        # Store the rule's name for the response message
        rule_name = rule_data.get("name", "Unknown rule")

        # Update only the enabled field
        rule_data["enabled"] = enabled

        # Send the update (PATCH) request
        patch_response = await http_client.patch(
            api_path,
            params=params,
            json=rule_data
        )
        patch_response.raise_for_status()

        # Confirm the update was successful
        updated_rule = patch_response.json()
        if updated_rule.get("enabled") == enabled:
            status_text = "enabled" if enabled else "disabled"
            return f"Successfully {status_text} rule '{rule_name}' ({identifier_text})"
        else:
            return f"Warning: Rule update completed but status may not be {action}d. Please verify."

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
        return f"{result_text}\nUnexpected error updating rule status: {str(e)}"
