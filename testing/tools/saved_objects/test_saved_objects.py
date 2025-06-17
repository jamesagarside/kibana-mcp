import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Import the tools to test
from kibana_mcp.tools.saved_objects.find_objects import _call_find_objects
from kibana_mcp.tools.saved_objects.get_object import _call_get_object
from kibana_mcp.tools.saved_objects.bulk_get_objects import _call_bulk_get_objects
from kibana_mcp.tools.saved_objects.create_object import _call_create_object
from kibana_mcp.tools.saved_objects.update_object import _call_update_object
from kibana_mcp.tools.saved_objects.delete_object import _call_delete_object
from kibana_mcp.tools.saved_objects.export_objects import _call_export_objects
from kibana_mcp.tools.saved_objects.import_objects import _call_import_objects

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response

# --- Tests for update_object ---


@pytest.mark.asyncio
async def test_update_object_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "dashboard-1",
        "type": "dashboard",
        "attributes": {
            "title": "Updated Dashboard",
            "description": "Updated description"
        },
        "references": [],
        "version": "WzIsMV0="
    }
    mock_client.put.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    attributes = {
        "title": "Updated Dashboard",
        "description": "Updated description"
    }
    result = await _call_update_object(
        mock_client,
        type="dashboard",
        id="dashboard-1",
        attributes=attributes
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "dashboard-1"
    assert result_dict["attributes"]["title"] == "Updated Dashboard"
    assert result_dict["version"] == "WzIsMV0="
    mock_client.put.assert_called_once()

    # Verify endpoint and payload
    args, kwargs = mock_client.put.call_args
    assert args[0] == "/api/saved_objects/dashboard/dashboard-1"
    assert kwargs["json"]["attributes"] == attributes


@pytest.mark.asyncio
async def test_update_object_with_version_and_references():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "dashboard-1",
        "type": "dashboard",
        "attributes": {
            "title": "Updated Dashboard"
        },
        "references": [
            {
                "name": "ref_0",
                "type": "visualization",
                "id": "viz-2"
            }
        ],
        "version": "WzMsMV0="
    }
    mock_client.put.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    attributes = {
        "title": "Updated Dashboard"
    }
    references = [
        {
            "name": "ref_0",
            "type": "visualization",
            "id": "viz-2"
        }
    ]
    result = await _call_update_object(
        mock_client,
        type="dashboard",
        id="dashboard-1",
        attributes=attributes,
        version="WzIsMV0=",
        references=references
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["id"] == "dashboard-1"
    assert len(result_dict["references"]) == 1
    assert result_dict["references"][0]["id"] == "viz-2"
    mock_client.put.assert_called_once()

    # Verify parameters
    args, kwargs = mock_client.put.call_args
    assert kwargs["params"]["version"] == "WzIsMV0="
    assert kwargs["json"]["attributes"] == attributes
    assert kwargs["json"]["references"] == references


# --- Tests for delete_object ---


@pytest.mark.asyncio
async def test_delete_object_success():
    # Arrange
    mock_client = AsyncMock()
    # Create a mock response that simulates a 204 No Content
    mock_response = create_mock_response(204, None)
    # Set a special flag to simulate empty content
    mock_response.content = False
    mock_client.delete.return_value = mock_response

    # Act
    result = await _call_delete_object(
        mock_client,
        type="dashboard",
        id="dashboard-1"
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["success"] is True
    assert "message" in result_dict
    mock_client.delete.assert_called_once()

    # Verify endpoint
    args, kwargs = mock_client.delete.call_args
    assert args[0] == "/api/saved_objects/dashboard/dashboard-1"


@pytest.mark.asyncio
async def test_delete_object_with_force():
    # Arrange
    mock_client = AsyncMock()
    # Create a mock response that simulates a 204 No Content
    mock_response = create_mock_response(204, None)
    # Set a special flag to simulate empty content
    mock_response.content = False
    mock_client.delete.return_value = mock_response

    # Act
    result = await _call_delete_object(
        mock_client,
        type="dashboard",
        id="dashboard-1",
        force=True
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["success"] is True
    assert "message" in result_dict
    mock_client.delete.assert_called_once()

    # Verify parameters
    args, kwargs = mock_client.delete.call_args
    assert kwargs["params"]["force"] == "true"


# --- Tests for bulk_get_objects ---


@pytest.mark.asyncio
async def test_bulk_get_objects_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "saved_objects": [
            {
                "id": "dashboard-1",
                "type": "dashboard",
                "attributes": {
                    "title": "Dashboard 1"
                }
            },
            {
                "id": "visualization-1",
                "type": "visualization",
                "attributes": {
                    "title": "Visualization 1"
                }
            }
        ]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    objects = [
        {"type": "dashboard", "id": "dashboard-1"},
        {"type": "visualization", "id": "visualization-1"}
    ]
    result = await _call_bulk_get_objects(
        mock_client,
        objects=objects
    )
    result_dict = json.loads(result)

    # Assert
    assert len(result_dict["saved_objects"]) == 2
    assert result_dict["saved_objects"][0]["id"] == "dashboard-1"
    assert result_dict["saved_objects"][1]["id"] == "visualization-1"
    mock_client.post.assert_called_once()

    # Verify endpoint and payload
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/saved_objects/_bulk_get"
    assert kwargs["json"]["objects"] == objects


# --- Tests for export_objects ---


@pytest.mark.asyncio
async def test_export_objects_success():
    # Arrange
    mock_client = AsyncMock()
    # Mocking NDJSON response (line-delimited JSON)
    mock_ndjson_response = (
        '{"type":"dashboard","id":"dashboard-1","attributes":{"title":"Dashboard 1"}}\n'
        '{"type":"visualization","id":"viz-1","attributes":{"title":"Visualization 1"}}'
    )
    mock_response = create_mock_response(200, None)
    # Set the content directly for NDJSON response
    mock_response.content = mock_ndjson_response.encode()
    mock_response.text = mock_ndjson_response
    mock_response.headers = {"content-type": "application/ndjson"}
    mock_response.read = MagicMock(return_value=mock_ndjson_response.encode())
    mock_client.post.return_value = mock_response

    # Act
    objects = [
        {"type": "dashboard", "id": "dashboard-1"},
        {"type": "visualization", "id": "viz-1"}
    ]
    result = await _call_export_objects(
        mock_client,
        objects=objects
    )
    result_list = json.loads(result)

    # Assert
    assert len(result_list) == 2
    assert result_list[0]["type"] == "dashboard"
    assert result_list[1]["type"] == "visualization"
    mock_client.post.assert_called_once()

    # Verify endpoint and payload
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/saved_objects/_export"
    assert kwargs["json"]["objects"] == objects


@pytest.mark.asyncio
async def test_export_objects_with_parameters():
    # Arrange
    mock_client = AsyncMock()
    mock_ndjson_response = '{"type":"dashboard","id":"dashboard-1","attributes":{"title":"Dashboard 1"}}'
    mock_response = create_mock_response(200, None)
    # Set the content directly for NDJSON response
    mock_response.content = mock_ndjson_response.encode()
    mock_response.text = mock_ndjson_response
    mock_response.headers = {"content-type": "application/ndjson"}
    mock_response.read = MagicMock(return_value=mock_ndjson_response.encode())
    mock_client.post.return_value = mock_response

    # Act
    objects = [{"type": "dashboard", "id": "dashboard-1"}]
    result = await _call_export_objects(
        mock_client,
        objects=objects,
        exclude_export_details=True,
        include_references=True,
        include_namespace=True
    )
    result_list = json.loads(result)

    # Assert
    assert len(result_list) == 1
    assert result_list[0]["type"] == "dashboard"
    mock_client.post.assert_called_once()

    # Verify parameters
    args, kwargs = mock_client.post.call_args
    params = kwargs["params"]
    assert params["exclude_export_details"] == "true"
    assert params["include_references"] == "true"
    assert params["include_namespace"] == "true"


# --- Tests for import_objects ---


@pytest.mark.asyncio
async def test_import_objects_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "success": True,
        "successCount": 2,
        "successResults": [
            {
                "type": "dashboard",
                "id": "dashboard-1",
                "meta": {
                    "title": "Dashboard 1",
                    "icon": "dashboardApp"
                }
            },
            {
                "type": "visualization",
                "id": "viz-1",
                "meta": {
                    "title": "Visualization 1",
                    "icon": "visualizeApp"
                }
            }
        ]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    objects_ndjson = (
        '{"type":"dashboard","id":"dashboard-1","attributes":{"title":"Dashboard 1"}}\n'
        '{"type":"visualization","id":"viz-1","attributes":{"title":"Visualization 1"}}'
    )
    result = await _call_import_objects(
        mock_client,
        objects_ndjson=objects_ndjson
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["success"] is True
    assert result_dict["successCount"] == 2
    assert len(result_dict["successResults"]) == 2
    mock_client.post.assert_called_once()

    # Verify the API was called with the right parameters
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/saved_objects/_import"
    assert "files" in kwargs
    assert kwargs["files"]["file"][0] == "import.ndjson"


@pytest.mark.asyncio
async def test_import_objects_with_parameters():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "success": True,
        "successCount": 1
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    objects_ndjson = '{"type":"dashboard","id":"dashboard-1","attributes":{"title":"Dashboard 1"}}'
    result = await _call_import_objects(
        mock_client,
        objects_ndjson=objects_ndjson,
        create_new_copies=True,
        overwrite=False
    )
    result_dict = json.loads(result)

    # Assert
    assert result_dict["success"] is True
    mock_client.post.assert_called_once()

    # Verify parameters
    args, kwargs = mock_client.post.call_args
    params = kwargs["params"]
    assert params["createNewCopies"] == "true"
    assert params["overwrite"] == "false"
