import httpx
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_response_action_details(
    http_client: httpx.AsyncClient,
    action_id: str
) -> str:
    """
    Get details of a response action by action ID.

    Args:
        http_client: The HTTP client to use for the API call
        action_id: The ID of the response action to retrieve

    Returns:
        JSON string with the detailed information about the response action
    """
    api_path = f"/api/endpoint/action/{action_id}"

    tool_logger.info(f"Fetching details for response action: {action_id}")

    try:
        response = await http_client.get(api_path)
        response.raise_for_status()
        result = response.json()

        # Format the response for better readability
        # Extract key details
        agents = result.get("agents", [])
        outputs = result.get("outputs", [])

        formatted_response = {
            "id": result.get("id"),
            "name": result.get("name"),
            "type": result.get("type"),
            "status": result.get("status"),
            "started_at": result.get("startedAt"),
            "completed_at": result.get("completedAt"),
            "user": result.get("userId"),
            "comment": result.get("comment"),
            "agents": [
                {
                    "id": agent.get("id"),
                    "type": agent.get("type"),
                    "status": agent.get("status")
                }
                for agent in agents
            ],
            "outputs": [
                {
                    "agent_id": output.get("agentId"),
                    "action_id": output.get("actionId"),
                    "output_type": output.get("type"),
                    "status": output.get("status"),
                    "content": output.get("output")
                }
                for output in outputs
            ]
        }

        # Add command data if available
        if "data" in result and "command" in result["data"]:
            formatted_response["command"] = result["data"]["command"]

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(
            f"Error fetching response action details for {action_id}: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": f"Failed to fetch response action details for action ID: {action_id}"
        }, indent=2)
