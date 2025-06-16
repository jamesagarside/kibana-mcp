import httpx
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_get_file_info(
    http_client: httpx.AsyncClient,
    action_id: str,
    file_id: str
) -> str:
    """
    Get information for a file retrieved by a response action.

    Args:
        http_client: The HTTP client to use for the API call
        action_id: The ID of the response action that retrieved the file
        file_id: The ID of the file to get information about

    Returns:
        JSON string with the detailed information about the file
    """
    api_path = f"/api/endpoint/action/{action_id}/file/{file_id}"

    tool_logger.info(
        f"Fetching file info for file {file_id} from action {action_id}")

    try:
        response = await http_client.get(api_path)
        response.raise_for_status()
        result = response.json()

        # Format the response for better readability
        formatted_response = {
            "file_id": result.get("id", file_id),
            "name": result.get("name", "unknown"),
            "size": result.get("size"),
            "created_at": result.get("createdAt"),
            "mime_type": result.get("mimeType"),
            "status": result.get("status"),
            "action_id": action_id,
            "agent_id": result.get("agentId"),
            "sha256": result.get("sha256"),
            "metadata": result.get("metadata", {})
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(
            f"Error fetching file info for file {file_id} from action {action_id}: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": f"Failed to fetch file information for file ID: {file_id} from action ID: {action_id}"
        }, indent=2)
