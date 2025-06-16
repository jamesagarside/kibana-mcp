import httpx
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_install_prepackaged_rules(
    http_client: httpx.AsyncClient
) -> str:
    """Handles the API interaction for installing or updating prepackaged rules and timelines."""
    api_path = "/api/detection_engine/rules/prepackaged"
    result_text = "Installing and updating prepackaged detection rules and timelines..."

    try:
        # Send the PUT request to install/update prepackaged rules and timelines
        response = await http_client.put(api_path)
        response.raise_for_status()

        # Process the response
        response_data = response.json()

        # Extract the installation results
        rules_installed = response_data.get("rules_installed", 0)
        rules_updated = response_data.get("rules_updated", 0)
        timelines_installed = response_data.get("timelines_installed", 0)
        timelines_updated = response_data.get("timelines_updated", 0)

        # Create a response message
        result_text = "Prepackaged content installation completed successfully.\n\n"
        result_text += "Detection Rules:\n"
        result_text += f"- {rules_installed} new rules installed\n"
        result_text += f"- {rules_updated} existing rules updated\n\n"

        result_text += "Timelines:\n"
        result_text += f"- {timelines_installed} new timelines installed\n"
        result_text += f"- {timelines_updated} existing timelines updated"

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
        return f"Unexpected error installing prepackaged rules: {str(e)}"
