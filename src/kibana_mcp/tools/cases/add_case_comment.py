import httpx
from typing import List, Optional, Dict, Any, Union
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_add_case_comment(
    http_client: httpx.AsyncClient,
    case_id: str,
    comment_type: str = "user",
    comment: Optional[str] = None,
    alert_ids: Optional[List[str]] = None,
    alert_index: Optional[str] = None,
    rule_id: Optional[str] = None,
    rule_name: Optional[str] = None,
    owner: str = "securitySolution"
) -> str:
    """Handles the API interaction for adding a comment or alert to a case."""
    api_path = f"/api/cases/{case_id}/comments"

    # Build the comment payload based on type
    if comment_type == "user":
        if not comment:
            return "Error: 'comment' is required for user comment type"
        payload = {
            "type": "user",
            "comment": comment,
            "owner": owner
        }
    elif comment_type == "alert":
        if not alert_ids or not alert_index:
            return "Error: 'alert_ids' and 'alert_index' are required for alert comment type"
        payload = {
            "type": "alert",
            "alertId": alert_ids,
            "index": alert_index,
            "owner": owner
        }
        if rule_id:
            payload["rule"] = {"id": rule_id}
            if rule_name:
                payload["rule"]["name"] = rule_name
    else:
        return f"Error: Invalid comment type '{comment_type}'. Must be 'user' or 'alert'"

    result_text = f"Adding {comment_type} comment to case {case_id}"

    try:
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        comment_data = response.json()
        result_text = json.dumps(comment_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
        result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
        result_text += f"\nUnexpected error during comment addition: {str(e)}"

    return result_text
