import httpx
from typing import List, Optional, Dict, Any
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_run_command_on_endpoint(
    http_client: httpx.AsyncClient,
    endpoint_ids: List[str],
    command: str,
    agent_type: str = "endpoint",
    comment: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Run a shell command on one or more endpoints.

    Args:
        http_client: The HTTP client to use for the API call
        endpoint_ids: List of endpoint IDs to run the command on
        command: Shell command to execute
        agent_type: The type of agent (default: "endpoint")
        comment: Optional comment to include with the action
        parameters: Additional parameters for the command

    Returns:
        JSON string with the response from the command action
    """
    api_path = "/api/endpoint/action"

    # Construct the request payload
    action_data = {
        "name": "execute",
        "type": "INPUT_ACTION",
        "agents": [{"agent_type": agent_type, "id": agent_id} for agent_id in endpoint_ids],
        "data": {
            "command": command
        }
    }

    # Add parameters if provided
    if parameters:
        action_data["data"].update(parameters)

    # Add comment if provided
    if comment:
        action_data["comment"] = comment

    tool_logger.info(
        f"Running command '{command}' on {len(endpoint_ids)} endpoints with comment: {comment}")

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
            "started_at": result.get("started_at"),
            "command": command,
            "agents": [{"id": agent.get("id"), "type": agent.get("type")} for agent in result.get("agents", [])],
            "status": "Command execution initiated",
            "message": f"Command execution started on {len(endpoint_ids)} endpoint(s)"
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(f"Error executing command on endpoints: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": f"Failed to execute command on {len(endpoint_ids)} endpoint(s)",
            "command": command
        }, indent=2)
