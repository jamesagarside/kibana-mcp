import httpx
from typing import List, Optional, Dict, Any
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_kill_process(
    http_client: httpx.AsyncClient,
    endpoint_ids: List[str],
    parameters: Dict[str, Any],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> str:
    """
    Terminate a running process on an endpoint.

    Args:
        http_client: The HTTP client to use for the API call
        endpoint_ids: List of endpoint IDs to terminate processes on
        parameters: Parameters for the kill process action, must include at least a process ID/name
        agent_type: The type of agent (default: "endpoint")
        comment: Optional comment to include with the action

    Returns:
        JSON string with the response from the kill process action
    """
    api_path = "/api/endpoint/action"

    # Validate parameters
    if not parameters:
        return json.dumps({
            "error": "Missing required parameters",
            "status": "failed",
            "message": "Process identification parameters are required"
        }, indent=2)

    # Construct the request payload
    action_data = {
        "name": "kill-process",
        "type": "INPUT_ACTION",
        "agents": [{"agent_type": agent_type, "id": agent_id} for agent_id in endpoint_ids],
        "data": parameters
    }

    # Add comment if provided
    if comment:
        action_data["comment"] = comment

    process_id = parameters.get("process_id", parameters.get(
        "processId", parameters.get("pid", "unknown")))
    process_name = parameters.get(
        "process_name", parameters.get("processName", "unknown"))

    tool_logger.info(
        f"Killing process {process_id or process_name} on {len(endpoint_ids)} endpoints with comment: {comment}")

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
            "process": process_id or process_name,
            "agents": [{"id": agent.get("id"), "type": agent.get("type")} for agent in result.get("agents", [])],
            "status": "Process termination initiated",
            "message": f"Process termination started on {len(endpoint_ids)} endpoint(s)"
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(f"Error killing process on endpoints: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": f"Failed to kill process on {len(endpoint_ids)} endpoint(s)",
            "process": process_id or process_name
        }, indent=2)
