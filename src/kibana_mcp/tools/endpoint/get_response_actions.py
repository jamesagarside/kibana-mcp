import httpx
from typing import List, Optional, Any, Dict
import json
import logging
from urllib.parse import urlencode

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_response_actions(
    http_client: httpx.AsyncClient,
    page: int = 1,
    page_size: int = 10,
    agent_ids: Optional[List[str]] = None,
    agent_types: Optional[str] = None,
    commands: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_ids: Optional[List[str]] = None,
    with_outputs: Optional[List[str]] = None
) -> str:
    """
    Get a list of all response actions from Elastic Defend endpoints.

    Args:
        http_client: The HTTP client to use for the API call
        page: Page number (minimum 1, default 1)
        page_size: Actions per page (default 10)
        agent_ids: Filter by agent IDs
        agent_types: Filter by agent type
        commands: Filter by command names
        types: Filter by action types
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        user_ids: Filter by user IDs
        with_outputs: Filter by output types

    Returns:
        JSON string with the list of response actions
    """
    base_path = "/api/endpoint/action"

    # Build query parameters
    query_params: Dict[str, Any] = {
        "page": page,
        "pageSize": page_size
    }

    # Add optional filters
    if agent_ids:
        query_params["agentIds"] = ','.join(agent_ids)
    if agent_types:
        query_params["agentType"] = agent_types
    if commands:
        query_params["commands"] = ','.join(commands)
    if types:
        query_params["types"] = ','.join(types)
    if start_date:
        query_params["startDate"] = start_date
    if end_date:
        query_params["endDate"] = end_date
    if user_ids:
        query_params["userIds"] = ','.join(user_ids)
    if with_outputs:
        query_params["withOutputs"] = ','.join(with_outputs)

    # Build query string
    query_string = urlencode(query_params)
    api_path = f"{base_path}?{query_string}"

    tool_logger.info(f"Fetching response actions with filters: {query_params}")

    try:
        response = await http_client.get(api_path)
        response.raise_for_status()
        result = response.json()

        # Format the response for better readability
        actions = result.get("items", [])
        formatted_response = {
            "total": result.get("total", 0),
            "page": page,
            "page_size": page_size,
            "actions": [
                {
                    "id": action.get("id"),
                    "name": action.get("name"),
                    "type": action.get("type"),
                    "status": action.get("status"),
                    "started_at": action.get("startedAt"),
                    "completed_at": action.get("completedAt", None),
                    "agents": [{"id": agent.get("id"), "type": agent.get("type")} for agent in action.get("agents", [])]
                }
                for action in actions
            ]
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(f"Error fetching response actions: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": "Failed to fetch response actions"
        }, indent=2)
