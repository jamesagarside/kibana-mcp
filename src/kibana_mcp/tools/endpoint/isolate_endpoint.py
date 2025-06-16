import httpx
from typing import List, Optional
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_isolate_endpoint(
    http_client: httpx.AsyncClient,
    endpoint_ids: List[str],
    agent_type: str = "endpoint",
    comment: Optional[str] = None
) -> str:
    """
    Isolate one or more endpoints from the network.

    Args:
        http_client: The HTTP client to use for the API call
        endpoint_ids: List of endpoint IDs to isolate
        agent_type: The type of agent (default: "endpoint")
        comment: Optional comment to include with the isolation action

    Returns:
        JSON string with the response from the isolation action
    """
    api_path = "/api/endpoint/action"

    # Construct the request payload
    action_data = {
        "name": "isolate",
        "type": "INPUT_ACTION",
        "agents": [{"agent_type": agent_type, "id": agent_id} for agent_id in endpoint_ids],
        "data": {},
    }

    # Add comment if provided
    if comment:
        action_data["comment"] = comment

    tool_logger.info(
        f"Isolating {len(endpoint_ids)} endpoints with comment: {comment}")

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
            "agents": [{"id": agent.get("id"), "type": agent.get("type")} for agent in result.get("agents", [])],
            "status": "Isolation action initiated",
            "message": f"Isolation action started for {len(endpoint_ids)} endpoint(s)"
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(f"Error isolating endpoints: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": f"Failed to isolate {len(endpoint_ids)} endpoint(s)"
        }, indent=2)
