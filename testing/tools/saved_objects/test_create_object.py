import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock

from kibana_mcp.tools.saved_objects.create_object import _call_create_object

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response


@pytest.mark.asyncio
async def test_create_object_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "dashboard-1",
        "type": "dashboard",
        "attributes": {
            "title": "New Dashboard",
            "description": "A new dashboard"
        },
        "references": [],
        "version": "WzEsMV0="
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    attributes = {
        "title": "New Dashboard",
        "description": "A new dashboard"
    }
    result = await _call_create_object(
        mock_client,
        type="dashboard",
        attributes=attributes
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "dashboard-1"
    assert result_dict["type"] == "dashboard"
    assert result_dict["attributes"]["title"] == "New Dashboard"
    mock_client.post.assert_called_once()

    # Verify endpoint and payload
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/saved_objects/dashboard"
    assert kwargs["json"]["attributes"] == attributes


@pytest.mark.asyncio
async def test_create_object_with_id():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "custom-id",
        "type": "dashboard",
        "attributes": {
            "title": "Dashboard with Custom ID"
        },
        "references": [],
        "version": "WzEsMV0="
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    attributes = {
        "title": "Dashboard with Custom ID"
    }
    result = await _call_create_object(
        mock_client,
        type="dashboard",
        attributes=attributes,
        id="custom-id"
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "custom-id"
    mock_client.post.assert_called_once()

    # Verify endpoint with ID
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/saved_objects/dashboard/custom-id"


@pytest.mark.asyncio
async def test_create_object_with_all_parameters():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "dashboard-with-refs",
        "type": "dashboard",
        "attributes": {
            "title": "Dashboard with References"
        },
        "references": [
            {
                "name": "ref_0",
                "type": "visualization",
                "id": "viz-1"
            }
        ],
        "version": "WzEsMV0="
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    attributes = {
        "title": "Dashboard with References"
    }
    references = [
        {
            "name": "ref_0",
            "type": "visualization",
            "id": "viz-1"
        }
    ]
    result = await _call_create_object(
        mock_client,
        type="dashboard",
        attributes=attributes,
        id="dashboard-with-refs",
        overwrite=True,
        references=references
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "dashboard-with-refs"
    assert len(result_dict["references"]) == 1
    mock_client.post.assert_called_once()

    # Verify all parameters
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/saved_objects/dashboard/dashboard-with-refs"
    assert kwargs["params"]["overwrite"] == "true"
    assert kwargs["json"]["attributes"] == attributes
    assert kwargs["json"]["references"] == references


@pytest.mark.asyncio
async def test_create_object_missing_type():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await _call_create_object(
        mock_client,
        type=None,
        attributes={"title": "Test"}
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "type" in result_dict["error"]
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_create_object_missing_attributes():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await _call_create_object(
        mock_client,
        type="dashboard",
        attributes=None
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "attributes" in result_dict["error"]
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_create_object_api_error():
    # Arrange
    mock_client = AsyncMock()
    mock_error_response = httpx.Response(
        status_code=409,
        content=json.dumps(
            {"error": "Conflict", "message": "Object already exists"}).encode()
    )
    mock_client.post.side_effect = httpx.HTTPStatusError(
        "Conflict", request=None, response=mock_error_response)

    # Act
    result = await _call_create_object(
        mock_client,
        type="dashboard",
        attributes={"title": "Test"}
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "409" in result_dict["error"]
    assert "Conflict" in result_dict["error"]
