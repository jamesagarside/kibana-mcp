import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock

from kibana_mcp.tools.saved_objects.get_object import _call_get_object

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response


@pytest.mark.asyncio
async def test_get_object_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "dashboard-1",
        "type": "dashboard",
        "attributes": {
            "title": "Test Dashboard",
            "description": "A test dashboard"
        },
        "references": []
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_object(
        mock_client,
        type="dashboard",
        id="dashboard-1"
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "dashboard-1"
    assert result_dict["type"] == "dashboard"
    assert result_dict["attributes"]["title"] == "Test Dashboard"
    mock_client.get.assert_called_once()

    # Verify endpoint URL
    args, kwargs = mock_client.get.call_args
    assert args[0] == "/api/saved_objects/dashboard/dashboard-1"


@pytest.mark.asyncio
async def test_get_object_with_parameters():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "dashboard-1",
        "type": "dashboard",
        "attributes": {
            "title": "Test Dashboard"
        },
        "references": [
            {
                "name": "ref_0",
                "type": "visualization",
                "id": "viz-1"
            }
        ]
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_object(
        mock_client,
        type="dashboard",
        id="dashboard-1",
        include_references=True,
        fields=["title"]
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "dashboard-1"
    assert "references" in result_dict
    mock_client.get.assert_called_once()

    # Verify parameters
    args, kwargs = mock_client.get.call_args
    params = kwargs["params"]
    assert params["include_references"] == "true"
    assert params["fields"] == "title"


@pytest.mark.asyncio
async def test_get_object_missing_parameters():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await _call_get_object(
        mock_client,
        type=None,
        id="dashboard-1"
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "type" in result_dict["error"]
    mock_client.get.assert_not_called()

    # Test with missing ID
    result = await _call_get_object(
        mock_client,
        type="dashboard",
        id=None
    )
    result_dict = json.loads(result)

    assert "error" in result_dict
    assert "id" in result_dict["error"]


@pytest.mark.asyncio
async def test_get_object_not_found():
    # Arrange
    mock_client = AsyncMock()
    mock_error_response = httpx.Response(
        status_code=404,
        content=json.dumps({"error": "Not found"}).encode()
    )
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Not found", request=None, response=mock_error_response)

    # Act
    result = await _call_get_object(
        mock_client,
        type="dashboard",
        id="nonexistent-id"
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "not found" in result_dict["error"].lower()


@pytest.mark.asyncio
async def test_get_object_api_error():
    # Arrange
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError("API Error")

    # Act
    result = await _call_get_object(
        mock_client,
        type="dashboard",
        id="dashboard-1"
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "API Error" in result_dict["error"]
