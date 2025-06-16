import httpx
from typing import Dict, Any
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_response_action_status(
    http_client: httpx.AsyncClient,
    query: Dict[str, Any]
) -> str:
    """
    Get the status of response actions for specified agent IDs.

    Args:
        http_client: The HTTP client to use for the API call
        query: Query object with filters like agent IDs, action types, etc.

    Returns:
        JSON string with the status of specified response actions
    """
    api_path = "/api/endpoint/action/status"

    tool_logger.info(f"Fetching response action status with query: {query}")

    try:
        response = await http_client.post(
            api_path,
            json=query
        )
        response.raise_for_status()
        result = response.json()

        # Format the response for better readability
        actions = result.get("data", [])
        formatted_response = {
            "actions": [
                {
                    "id": action.get("id"),
                    "name": action.get("name"),
                    "type": action.get("type"),
                    "status": action.get("status", "unknown"),
                    "started_at": action.get("startedAt"),
                    "completed_at": action.get("completedAt"),
                    "agents": [
                        {
                            "id": agent.get("id"),
                            "type": agent.get("type"),
                            "status": agent.get("status", "unknown")
                        }
                        for agent in action.get("agents", [])
                    ]
                }
                for action in actions
            ]
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(f"Error fetching response action status: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": "Failed to fetch response action status"
        }, indent=2)
