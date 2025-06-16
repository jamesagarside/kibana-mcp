import httpx
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_prepackaged_rules_status(
    http_client: httpx.AsyncClient
) -> str:
    """Handles the API interaction for checking the status of prepackaged rules and timelines."""
    api_path = "/api/detection_engine/rules/prepackaged/_status"
    result_text = "Checking status of prepackaged detection rules and timelines..."

    try:
        # Get the prepackaged rules status
        response = await http_client.get(api_path)
        response.raise_for_status()

        # Process the response
        response_data = response.json()

        # Format the result in a user-friendly way
        formatted_result = {
            "rules_custom_installed": response_data.get("rules_custom_installed", 0),
            "rules_installed": response_data.get("rules_installed", 0),
            "rules_not_installed": response_data.get("rules_not_installed", 0),
            "rules_not_updated": response_data.get("rules_not_updated", 0),
            "timelines_installed": response_data.get("timelines_installed", 0),
            "timelines_not_installed": response_data.get("timelines_not_installed", 0),
            "timelines_not_updated": response_data.get("timelines_not_updated", 0)
        }

        # Create a text summary
        result_text = "Prepackaged Detection Rules Status:\n"
        result_text += f"- Custom rules installed: {formatted_result['rules_custom_installed']}\n"
        result_text += f"- Prepackaged rules installed: {formatted_result['rules_installed']}\n"
        result_text += f"- Prepackaged rules available but not installed: {formatted_result['rules_not_installed']}\n"
        result_text += f"- Prepackaged rules installed but outdated: {formatted_result['rules_not_updated']}\n\n"

        result_text += "Prepackaged Timelines Status:\n"
        result_text += f"- Prepackaged timelines installed: {formatted_result['timelines_installed']}\n"
        result_text += f"- Prepackaged timelines available but not installed: {formatted_result['timelines_not_installed']}\n"
        result_text += f"- Prepackaged timelines installed but outdated: {formatted_result['timelines_not_updated']}\n"

        # Add detailed information if available
        if "rules_custom_installed_missing_exceptions_list" in response_data:
            result_text += "\nCustom rules missing exceptions: "
            result_text += f"{len(response_data.get('rules_custom_installed_missing_exceptions_list', []))}\n"

        return result_text

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
        return f"Unexpected error getting prepackaged rules status: {str(e)}"
