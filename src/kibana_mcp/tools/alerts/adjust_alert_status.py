import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_adjust_alert_status(http_client: httpx.AsyncClient, alert_id: str, new_status: str) -> str:
    """Handles the API interaction for adjusting alert signal status."""
    # Use the specific endpoint for setting signal status
    api_path = "/api/detection_engine/signals/status"
    
    # Validate status input slightly
    valid_statuses = ["open", "acknowledged", "closed"] # Add "in-progress" if needed
    if new_status not in valid_statuses:
        return f"Error: Invalid status '{new_status}'. Must be one of {valid_statuses}."

    result_text = f"Attempting to change status of alert signal {alert_id} to {new_status}..."

    # Construct the payload for the signals/status endpoint
    payload = {
        "signal_ids": [alert_id],
        "status": new_status
    }

    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        response_data = response.json()
        # Try to extract a meaningful success message, e.g., based on 'updated' count
        updated_count = response_data.get("updated", 0)
        if updated_count > 0:
            success_msg = f"Successfully updated status for {updated_count} signal(s)."
        else:
            success_msg = "Status update request processed, but no signals were updated (check ID or current status)."
        result_text += f"\nKibana API response: {response.status_code} - {success_msg}"

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except Exception as e:
         result_text += f"\nUnexpected error during status update: {str(e)}"

    return result_text 