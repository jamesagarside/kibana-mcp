import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the endpoint tools to test
from kibana_mcp.tools.endpoint.isolate_endpoint import _call_isolate_endpoint
from kibana_mcp.tools.endpoint.unisolate_endpoint import _call_unisolate_endpoint
from kibana_mcp.tools.endpoint.run_command_on_endpoint import _call_run_command_on_endpoint
from kibana_mcp.tools.endpoint.get_response_actions import _call_get_response_actions
from kibana_mcp.tools.endpoint.get_response_action_details import _call_get_response_action_details
from kibana_mcp.tools.endpoint.get_response_action_status import _call_get_response_action_status
from kibana_mcp.tools.endpoint.kill_process import _call_kill_process
from kibana_mcp.tools.endpoint.suspend_process import _call_suspend_process
from kibana_mcp.tools.endpoint.scan_endpoint import _call_scan_endpoint
from kibana_mcp.tools.endpoint.get_file_info import _call_get_file_info
from kibana_mcp.tools.endpoint.download_file import _call_download_file

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response

# --- Tests for isolate_endpoint ---


@pytest.mark.asyncio
async def test_isolate_endpoint_success():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123", "endpoint-456"]
    comment = "Isolating for investigation"
    mock_response_data = {
        "id": "action-123",
        "started_at": "2025-06-16T10:00:00.000Z",
        "agents": [
            {"id": "endpoint-123", "type": "endpoint"},
            {"id": "endpoint-456", "type": "endpoint"}
        ]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_isolate_endpoint(
        mock_client, endpoint_ids, agent_type="endpoint", comment=comment)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["action_id"] == "action-123"
    assert "Isolation action initiated" in result_dict["status"]
    assert len(result_dict["agents"]) == 2
    mock_client.post.assert_called_once_with(
        "/api/endpoint/action",
        json={
            "name": "isolate",
            "type": "INPUT_ACTION",
            "agents": [{"agent_type": "endpoint", "id": id} for id in endpoint_ids],
            "data": {},
            "comment": comment
        }
    )


@pytest.mark.asyncio
async def test_isolate_endpoint_error():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    mock_client.post.return_value = create_mock_response(
        400, {"message": "Bad request"})
    mock_client.post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_client.post.return_value)

    # Act
    result = await _call_isolate_endpoint(mock_client, endpoint_ids)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Failed to isolate" in result_dict["message"]
    mock_client.post.assert_called_once()

# --- Tests for unisolate_endpoint ---


@pytest.mark.asyncio
async def test_unisolate_endpoint_success():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123", "endpoint-456"]
    comment = "Investigation complete"
    mock_response_data = {
        "id": "action-456",
        "started_at": "2025-06-16T12:00:00.000Z",
        "agents": [
            {"id": "endpoint-123", "type": "endpoint"},
            {"id": "endpoint-456", "type": "endpoint"}
        ]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_unisolate_endpoint(
        mock_client, endpoint_ids, agent_type="endpoint", comment=comment)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["action_id"] == "action-456"
    assert "Release from isolation action initiated" in result_dict["status"]
    assert len(result_dict["agents"]) == 2
    mock_client.post.assert_called_once_with(
        "/api/endpoint/action",
        json={
            "name": "unisolate",
            "type": "INPUT_ACTION",
            "agents": [{"agent_type": "endpoint", "id": id} for id in endpoint_ids],
            "data": {},
            "comment": comment
        }
    )


@pytest.mark.asyncio
async def test_unisolate_endpoint_error():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    mock_client.post.return_value = create_mock_response(
        400, {"message": "Bad request"})
    mock_client.post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_client.post.return_value)

    # Act
    result = await _call_unisolate_endpoint(mock_client, endpoint_ids)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Failed to release" in result_dict["message"]
    mock_client.post.assert_called_once()

# --- Tests for run_command_on_endpoint ---


@pytest.mark.asyncio
async def test_run_command_on_endpoint_success():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    command = "whoami"
    mock_response_data = {
        "id": "action-789",
        "started_at": "2025-06-16T14:00:00.000Z",
        "agents": [{"id": "endpoint-123", "type": "endpoint"}],
        "data": {"command": "whoami"}
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_run_command_on_endpoint(
        mock_client, endpoint_ids, command, agent_type="endpoint")
    result_dict = json.loads(result)

    # Assert
    assert result_dict["action_id"] == "action-789"
    assert "Command execution initiated" in result_dict["status"]
    assert result_dict["command"] == "whoami"
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_run_command_on_endpoint_error():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    command = "invalid-command"
    mock_client.post.return_value = create_mock_response(
        400, {"message": "Bad request"})
    mock_client.post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_client.post.return_value)

    # Act
    result = await _call_run_command_on_endpoint(mock_client, endpoint_ids, command)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Failed to execute command" in result_dict["message"]
    mock_client.post.assert_called_once()

# --- Tests for get_response_actions ---


@pytest.mark.asyncio
async def test_get_response_actions_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "total": 2,
        "items": [
            {
                "id": "action-123",
                "name": "isolate",
                "type": "INPUT_ACTION",
                "status": "completed",
                "startedAt": "2025-06-16T10:00:00.000Z",
                "completedAt": "2025-06-16T10:01:00.000Z",
                "agents": [{"id": "endpoint-123", "type": "endpoint"}]
            },
            {
                "id": "action-456",
                "name": "run-command",
                "type": "INPUT_ACTION",
                "status": "running",
                "startedAt": "2025-06-16T12:00:00.000Z",
                "agents": [{"id": "endpoint-456", "type": "endpoint"}]
            }
        ]
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_response_actions(mock_client, page=1, page_size=10)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["total"] == 2
    assert len(result_dict["actions"]) == 2
    assert result_dict["actions"][0]["id"] == "action-123"
    assert result_dict["actions"][1]["id"] == "action-456"
    mock_client.get.assert_called_once()
    # Check that the URL has the correct query parameters
    args, kwargs = mock_client.get.call_args
    assert "page=1" in args[0]
    assert "pageSize=10" in args[0]


@pytest.mark.asyncio
async def test_get_response_actions_with_filters():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "total": 1,
        "items": [
            {
                "id": "action-123",
                "name": "isolate",
                "type": "INPUT_ACTION",
                "status": "completed",
                "startedAt": "2025-06-16T10:00:00.000Z",
                "completedAt": "2025-06-16T10:01:00.000Z",
                "agents": [{"id": "endpoint-123", "type": "endpoint"}]
            }
        ]
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_response_actions(
        mock_client,
        page=1,
        page_size=10,
        agent_ids=["endpoint-123"],
        commands=["isolate"]
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["total"] == 1
    assert len(result_dict["actions"]) == 1
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert "agentIds=endpoint-123" in args[0]
    assert "commands=isolate" in args[0]

# --- Tests for get_response_action_details ---


@pytest.mark.asyncio
async def test_get_response_action_details_success():
    # Arrange
    mock_client = AsyncMock()
    action_id = "action-123"
    mock_response_data = {
        "id": "action-123",
        "name": "isolate",
        "type": "INPUT_ACTION",
        "status": "completed",
        "startedAt": "2025-06-16T10:00:00.000Z",
        "completedAt": "2025-06-16T10:01:00.000Z",
        "userId": "user-1",
        "comment": "Isolating compromised endpoint",
        "agents": [
            {"id": "endpoint-123", "type": "endpoint", "status": "completed"}
        ],
        "outputs": [
            {
                "agentId": "endpoint-123",
                "actionId": "action-123",
                "type": "isolate-result",
                "status": "completed",
                "output": "Endpoint isolated successfully"
            }
        ]
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_response_action_details(mock_client, action_id)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "action-123"
    assert result_dict["name"] == "isolate"
    assert len(result_dict["agents"]) == 1
    assert len(result_dict["outputs"]) == 1
    mock_client.get.assert_called_once_with(
        f"/api/endpoint/action/{action_id}")


@pytest.mark.asyncio
async def test_get_response_action_details_error():
    # Arrange
    mock_client = AsyncMock()
    action_id = "nonexistent-action"
    mock_client.get.return_value = create_mock_response(
        404, {"message": "Action not found"})
    mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_client.get.return_value)

    # Act
    result = await _call_get_response_action_details(mock_client, action_id)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Failed to fetch response action details" in result_dict["message"]
    mock_client.get.assert_called_once_with(
        f"/api/endpoint/action/{action_id}")

# --- Tests for get_response_action_status ---


@pytest.mark.asyncio
async def test_get_response_action_status_success():
    # Arrange
    mock_client = AsyncMock()
    query = {"agentIds": ["endpoint-123", "endpoint-456"]}
    mock_response_data = {
        "data": [
            {
                "id": "action-123",
                "name": "isolate",
                "type": "INPUT_ACTION",
                "status": "completed",
                "startedAt": "2025-06-16T10:00:00.000Z",
                "completedAt": "2025-06-16T10:01:00.000Z",
                "agents": [
                    {"id": "endpoint-123", "type": "endpoint", "status": "completed"}
                ]
            },
            {
                "id": "action-456",
                "name": "run-command",
                "type": "INPUT_ACTION",
                "status": "running",
                "startedAt": "2025-06-16T12:00:00.000Z",
                "agents": [
                    {"id": "endpoint-456", "type": "endpoint", "status": "running"}
                ]
            }
        ]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_response_action_status(mock_client, query)
    result_dict = json.loads(result)

    # Assert
    assert len(result_dict["actions"]) == 2
    assert result_dict["actions"][0]["id"] == "action-123"
    assert result_dict["actions"][0]["status"] == "completed"
    assert result_dict["actions"][1]["id"] == "action-456"
    assert result_dict["actions"][1]["status"] == "running"
    mock_client.post.assert_called_once_with(
        "/api/endpoint/action/status",
        json=query
    )


@pytest.mark.asyncio
async def test_get_response_action_status_error():
    # Arrange
    mock_client = AsyncMock()
    query = {"invalidParam": "value"}
    mock_client.post.return_value = create_mock_response(
        400, {"message": "Invalid query parameters"})
    mock_client.post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_client.post.return_value)

    # Act
    result = await _call_get_response_action_status(mock_client, query)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Failed to fetch response action status" in result_dict["message"]
    mock_client.post.assert_called_once()

# --- Tests for kill_process ---


@pytest.mark.asyncio
async def test_kill_process_success():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    parameters = {"pid": 1234}
    mock_response_data = {
        "id": "action-123",
        "startedAt": "2025-06-16T10:00:00.000Z",
        "agents": [{"id": "endpoint-123", "type": "endpoint"}]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_kill_process(mock_client, endpoint_ids, parameters)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["action_id"] == "action-123"
    assert "Process termination initiated" in result_dict["status"]
    assert result_dict["process"] == 1234
    mock_client.post.assert_called_once_with(
        "/api/endpoint/action",
        json={
            "name": "kill-process",
            "type": "INPUT_ACTION",
            "agents": [{"agent_type": "endpoint", "id": id} for id in endpoint_ids],
            "data": parameters
        }
    )


@pytest.mark.asyncio
async def test_kill_process_missing_parameters():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    parameters = {}  # Empty parameters

    # Act
    result = await _call_kill_process(mock_client, endpoint_ids, parameters)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Process identification parameters are required" in result_dict["message"]
    # The client should not be called if parameters are missing
    mock_client.post.assert_not_called()

# --- Tests for suspend_process ---


@pytest.mark.asyncio
async def test_suspend_process_success():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    parameters = {"pid": 5678}
    mock_response_data = {
        "id": "action-123",
        "startedAt": "2025-06-16T10:00:00.000Z",
        "agents": [{"id": "endpoint-123", "type": "endpoint"}]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_suspend_process(mock_client, endpoint_ids, parameters)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["action_id"] == "action-123"
    assert "Process suspension initiated" in result_dict["status"]
    assert result_dict["process"] == 5678
    mock_client.post.assert_called_once_with(
        "/api/endpoint/action",
        json={
            "name": "suspend-process",
            "type": "INPUT_ACTION",
            "agents": [{"agent_type": "endpoint", "id": id} for id in endpoint_ids],
            "data": parameters
        }
    )


@pytest.mark.asyncio
async def test_suspend_process_missing_parameters():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    parameters = {}  # Empty parameters

    # Act
    result = await _call_suspend_process(mock_client, endpoint_ids, parameters)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Process identification parameters are required" in result_dict["message"]
    # The client should not be called if parameters are missing
    mock_client.post.assert_not_called()

# --- Tests for scan_endpoint ---


@pytest.mark.asyncio
async def test_scan_endpoint_success():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    parameters = {"path": "/suspicious/directory"}
    mock_response_data = {
        "id": "action-123",
        "startedAt": "2025-06-16T10:00:00.000Z",
        "agents": [{"id": "endpoint-123", "type": "endpoint"}]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_scan_endpoint(mock_client, endpoint_ids, parameters)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["action_id"] == "action-123"
    assert "Scan initiated" in result_dict["status"]
    assert result_dict["path"] == "/suspicious/directory"
    mock_client.post.assert_called_once_with(
        "/api/endpoint/action",
        json={
            "name": "scan-file",
            "type": "INPUT_ACTION",
            "agents": [{"agent_type": "endpoint", "id": id} for id in endpoint_ids],
            "data": parameters
        }
    )


@pytest.mark.asyncio
async def test_scan_endpoint_missing_parameters():
    # Arrange
    mock_client = AsyncMock()
    endpoint_ids = ["endpoint-123"]
    parameters = {}  # Empty parameters

    # Act
    result = await _call_scan_endpoint(mock_client, endpoint_ids, parameters)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Scan path parameter is required" in result_dict["message"]
    # The client should not be called if parameters are missing
    mock_client.post.assert_not_called()

# --- Tests for get_file_info ---


@pytest.mark.asyncio
async def test_get_file_info_success():
    # Arrange
    mock_client = AsyncMock()
    action_id = "action-123"
    file_id = "file-456"
    mock_response_data = {
        "id": "file-456",
        "name": "suspicious.exe",
        "size": 1024,
        "createdAt": "2025-06-16T10:00:00.000Z",
        "mimeType": "application/x-msdownload",
        "status": "ready",
        "agentId": "endpoint-123",
        "sha256": "abc123def456",
        "metadata": {"malicious": False}
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_file_info(mock_client, action_id, file_id)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["file_id"] == "file-456"
    assert result_dict["name"] == "suspicious.exe"
    assert result_dict["sha256"] == "abc123def456"
    assert not result_dict["metadata"]["malicious"]
    mock_client.get.assert_called_once_with(
        f"/api/endpoint/action/{action_id}/file/{file_id}")


@pytest.mark.asyncio
async def test_get_file_info_error():
    # Arrange
    mock_client = AsyncMock()
    action_id = "action-123"
    file_id = "nonexistent-file"
    mock_client.get.return_value = create_mock_response(
        404, {"message": "File not found"})
    mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_client.get.return_value)

    # Act
    result = await _call_get_file_info(mock_client, action_id, file_id)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Failed to fetch file information" in result_dict["message"]
    mock_client.get.assert_called_once()

# --- Tests for download_file ---


@pytest.mark.asyncio
async def test_download_file_success():
    # Arrange
    mock_client = AsyncMock()
    action_id = "action-123"
    file_id = "file-456"

    # First call for file info
    info_mock_response = create_mock_response(200, {
        "id": "file-456",
        "name": "suspicious.exe",
        "size": 1024,
        "createdAt": "2025-06-16T10:00:00.000Z",
        "mimeType": "application/x-msdownload",
        "status": "ready",
        "agentId": "endpoint-123",
        "sha256": "abc123def456"
    })

    # Second call for download
    download_mock_response = MagicMock()
    download_mock_response.status_code = 200
    download_mock_response.content = b"sample file content"
    download_mock_response.raise_for_status = MagicMock()

    # Configure the mock client to return different responses for different calls
    mock_client.get.side_effect = [info_mock_response, download_mock_response]

    # Act
    result = await _call_download_file(mock_client, action_id, file_id)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["file_id"] == "file-456"
    assert result_dict["name"] == "suspicious.exe"
    assert result_dict["download_successful"] is True
    assert result_dict["content_size"] == len(b"sample file content")
    # Base64 encoded "sample file content" is "c2FtcGxlIGZpbGUgY29udGVudA=="
    assert "c2FtcGxlIGZpbGUgY29udGVudA==" in result_dict["content_base64"]
    assert mock_client.get.call_count == 2

    # Check the URLs that were called
    calls = mock_client.get.call_args_list
    assert calls[0][0][0] == f"/api/endpoint/action/{action_id}/file/{file_id}"
    assert calls[1][0][0] == f"/api/endpoint/action/{action_id}/file/{file_id}/download"


@pytest.mark.asyncio
async def test_download_file_error():
    # Arrange
    mock_client = AsyncMock()
    action_id = "action-123"
    file_id = "file-456"

    # Configure the mock to raise an error
    mock_client.get.return_value = create_mock_response(
        404, {"message": "File not found"})
    mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_client.get.return_value)

    # Act
    result = await _call_download_file(mock_client, action_id, file_id)
    result_dict = json.loads(result)

    # Assert
    assert result_dict["status"] == "failed"
    assert "Failed to download file" in result_dict["message"]
    mock_client.get.assert_called_once()
