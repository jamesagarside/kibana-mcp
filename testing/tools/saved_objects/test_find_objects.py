import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock

from kibana_mcp.tools.saved_objects.find_objects import _call_find_objects

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response


@pytest.mark.asyncio
async def test_find_objects_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "total": 2,
        "per_page": 20,
        "page": 1,
        "saved_objects": [
            {
                "id": "dashboard-1",
                "type": "dashboard",
                "attributes": {
                    "title": "Test Dashboard 1",
                    "description": "A test dashboard"
                },
                "references": []
            },
            {
                "id": "dashboard-2",
                "type": "dashboard",
                "attributes": {
                    "title": "Test Dashboard 2",
                    "description": "Another test dashboard"
                },
                "references": []
            }
        ]
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_find_objects(
        mock_client,
        type=["dashboard"],
        search="Test"
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["total"] == 2
    assert len(result_dict["saved_objects"]) == 2
    assert result_dict["saved_objects"][0]["id"] == "dashboard-1"
    assert result_dict["saved_objects"][1]["id"] == "dashboard-2"
    mock_client.get.assert_called_once()

    # Verify query parameters
    args, kwargs = mock_client.get.call_args
    assert args[0] == "/api/saved_objects/_find"
    assert kwargs["params"]["type"] == "dashboard"
    assert kwargs["params"]["search"] == "Test"


@pytest.mark.asyncio
async def test_find_objects_with_all_parameters():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "total": 1,
        "per_page": 10,
        "page": 1,
        "saved_objects": [
            {
                "id": "dashboard-1",
                "type": "dashboard",
                "attributes": {
                    "title": "Test Dashboard 1"
                }
            }
        ]
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_find_objects(
        mock_client,
        type=["dashboard"],
        search="Test",
        search_fields=["title"],
        default_search_operator="AND",
        page=1,
        per_page=10,
        sort_field="title",
        sort_order="asc",
        fields=["title"],
        filter="attributes.title:Test*",
        has_reference={"type": "visualization", "id": "viz-1"}
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["total"] == 1
    mock_client.get.assert_called_once()

    # Verify all parameters were passed correctly
    args, kwargs = mock_client.get.call_args
    params = kwargs["params"]
    assert params["type"] == "dashboard"
    assert params["search"] == "Test"
    assert params["search_fields"] == "title"
    assert params["default_search_operator"] == "AND"
    assert params["page"] == 1
    assert params["per_page"] == 10
    assert params["sort_field"] == "title"
    assert params["sort_order"] == "asc"
    assert params["fields"] == "title"
    assert params["filter"] == "attributes.title:Test*"
    assert params["has_reference[type]"] == "visualization"
    assert params["has_reference[id]"] == "viz-1"


@pytest.mark.asyncio
async def test_find_objects_missing_type():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await _call_find_objects(
        mock_client,
        type=None
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "type" in result_dict["error"]
    mock_client.get.assert_not_called()


@pytest.mark.asyncio
async def test_find_objects_api_error():
    # Arrange
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError("API Error")

    # Act
    result = await _call_find_objects(
        mock_client,
        type=["dashboard"]
    )
    result_dict = json.loads(result)

    # Assert
    assert "error" in result_dict
    assert "API Error" in result_dict["error"]
