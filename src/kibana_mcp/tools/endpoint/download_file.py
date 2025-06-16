import httpx
import json
import logging
import base64

tool_logger = logging.getLogger("kibana-mcp.tools")


async def _call_download_file(
    http_client: httpx.AsyncClient,
    action_id: str,
    file_id: str
) -> str:
    """
    Download a file from an endpoint.

    Args:
        http_client: The HTTP client to use for the API call
        action_id: The ID of the response action that retrieved the file
        file_id: The ID of the file to download

    Returns:
        JSON string with the file information and base64-encoded content
    """
    # First, get the file info to include in the response
    info_api_path = f"/api/endpoint/action/{action_id}/file/{file_id}"
    download_api_path = f"/api/endpoint/action/{action_id}/file/{file_id}/download"

    tool_logger.info(f"Downloading file {file_id} from action {action_id}")

    try:
        # Get file info
        info_response = await http_client.get(info_api_path)
        info_response.raise_for_status()
        info = info_response.json()

        # Download file
        download_response = await http_client.get(download_api_path)
        download_response.raise_for_status()
        file_content = download_response.content

        # Encode file content as base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')

        # Format the response with file info and encoded content
        formatted_response = {
            "file_id": info.get("id", file_id),
            "name": info.get("name", "unknown"),
            "size": info.get("size"),
            "created_at": info.get("createdAt"),
            "mime_type": info.get("mimeType"),
            "action_id": action_id,
            "agent_id": info.get("agentId"),
            "sha256": info.get("sha256"),
            "download_successful": True,
            "content_size": len(file_content),
            "content_base64": encoded_content[:100] + "..." if len(encoded_content) > 100 else encoded_content,
            "message": f"File downloaded successfully. File size: {len(file_content)} bytes"
        }

        return json.dumps(formatted_response, indent=2)

    except httpx.HTTPError as e:
        tool_logger.error(
            f"Error downloading file {file_id} from action {action_id}: {e}")
        return json.dumps({
            "error": str(e),
            "status": "failed",
            "message": f"Failed to download file ID: {file_id} from action ID: {action_id}"
        }, indent=2)
