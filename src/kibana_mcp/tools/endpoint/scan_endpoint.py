import httpx
from typing import List, Optional, Dict, Any
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_scan_endpoint(
    http_client: httpx.AsyncClient,
    endpoint_ids: List[str],
    parameters: Dict[str, Any],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> str:
    """
    Scan a file or directory on an endpoint for malware.

    Args:
        http_client: The HTTP client to use for the API call
        endpoint_ids: List of endpoint IDs to scan
        parameters: Parameters for the scan action, should include path to scan
        agent_type: The type of agent (default: "endpoint")
        comment: Optional comment to include with the action

    Returns:
        JSON string with the response from the scan action
    """
    api_path = "/api/endpoint/action"

    # Validate parameters
    if not parameters or not (parameters.get("path") or parameters.get("paths")):
        return json.dumps({
            "error": "Missing required parameters",
            "status": "failed",
            "message": "Scan path parameter is required"
        }, indent=2)

    # Construct the request payload
    action_data = {
        "name": "scan-file",
        "type": "INPUT_ACTION",
        "agents": [{"agent_type": agent_type, "id": agent_id} for agent_id in endpoint_ids],
        "data": parameters
    }

    # Add comment if provided
    if comment:
        action_data["comment"] = comment

    scan_path = parameters.get("path", parameters.get("paths", ["unknown"])[0])

    tool_logger.info(
        f"Scanning {scan_path} on {len(endpoint_ids)} endpoints with comment: {comment}")

    try:
        response = await http_client.post(
            api_path,
            json=action_data
        )
        response.raise_for_status()
        result = response.json()

        # Format the response for better readability
        formatted_response = {
            "action_id": result.get("id"),
            "started_at": result.get("startedAt"),
            "path": scan_path,
            "agents": [{"id": agent.get("id"), "type": agent.get("type")} for agent in result.get("agents", [])],
            "status": "Scan initiated",
            "message": f"Scan started on {len(endpoint_ids)} endpoint(s)"
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(f"Error scanning endpoint: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": f"Failed to scan {len(endpoint_ids)} endpoint(s)",
            "path": scan_path
        }, indent=2)
