import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the tools to test
from kibana_mcp.tools.rules.get_rule import _call_get_rule
from kibana_mcp.tools.rules.delete_rule import _call_delete_rule
from kibana_mcp.tools.rules.update_rule_status import _call_update_rule_status
from kibana_mcp.tools.rules.find_rules import _call_find_rules
from kibana_mcp.tools.rules.get_prepackaged_rules_status import _call_get_prepackaged_rules_status
from kibana_mcp.tools.rules.install_prepackaged_rules import _call_install_prepackaged_rules

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response

# --- Tests for get_rule ---


@pytest.mark.asyncio
async def test_get_rule_with_rule_id_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "1234-5678-90ab-cdef",
        "rule_id": "test-rule-id",
        "name": "Test Rule",
        "description": "Test rule description",
        "enabled": True,
        "risk_score": 50,
        "severity": "medium",
        "type": "query"
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_rule(mock_client, rule_id="test-rule-id")

    # Assert
    assert "Rule fetched successfully" in result
    assert "Test Rule" in result
    assert "test-rule-id" in result
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert kwargs["params"]["rule_id"] == "test-rule-id"


@pytest.mark.asyncio
async def test_get_rule_with_id_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "1234-5678-90ab-cdef",
        "rule_id": "test-rule-id",
        "name": "Test Rule"
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_rule(mock_client, id="1234-5678-90ab-cdef")

    # Assert
    assert "Rule fetched successfully" in result
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert kwargs["params"]["id"] == "1234-5678-90ab-cdef"


@pytest.mark.asyncio
async def test_get_rule_missing_parameters():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await _call_get_rule(mock_client)

    # Assert
    assert "Error: You must provide either rule_id or id parameter" in result
    mock_client.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_rule_api_error():
    # Arrange
    mock_client = AsyncMock()
    mock_response = create_mock_response(404, {"message": "Rule not found"})
    mock_client.get.return_value = mock_response
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_response
    )

    # Act
    result = await _call_get_rule(mock_client, rule_id="non-existent-rule")

    # Assert
    assert "Kibana API" in result
    assert "returned error: 404" in result

# --- Tests for delete_rule ---


@pytest.mark.asyncio
async def test_delete_rule_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "1234-5678-90ab-cdef",
        "rule_id": "test-rule-id",
        "name": "Test Rule"
    }
    mock_client.delete.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_delete_rule(mock_client, rule_id="test-rule-id")

    # Assert
    assert "Successfully deleted rule" in result
    assert "Test Rule" in result
    mock_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_rule_missing_parameters():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await _call_delete_rule(mock_client)

    # Assert
    assert "Error: You must provide either rule_id or id parameter" in result
    mock_client.delete.assert_not_called()

# --- Tests for update_rule_status ---


@pytest.mark.asyncio
async def test_update_rule_status_enable():
    # Arrange
    mock_client = AsyncMock()
    mock_get_response = {
        "id": "1234-5678-90ab-cdef",
        "rule_id": "test-rule-id",
        "name": "Test Rule",
        "enabled": False,
        "description": "Test Description"
    }
    mock_patch_response = {
        "id": "1234-5678-90ab-cdef",
        "rule_id": "test-rule-id",
        "name": "Test Rule",
        "enabled": True,
        "description": "Test Description"
    }

    # Set up the mock client to return appropriate responses for GET and PATCH
    mock_client.get.return_value = create_mock_response(200, mock_get_response)
    mock_client.patch.return_value = create_mock_response(
        200, mock_patch_response)

    # Act
    result = await _call_update_rule_status(mock_client, rule_id="test-rule-id", enabled=True)

    # Assert
    assert "Successfully enabled rule" in result
    assert "Test Rule" in result
    mock_client.get.assert_called_once()
    mock_client.patch.assert_called_once()

    # Verify the PATCH request contains the updated enabled field
    args, kwargs = mock_client.patch.call_args
    assert kwargs["json"]["enabled"] is True


@pytest.mark.asyncio
async def test_update_rule_status_disable():
    # Arrange
    mock_client = AsyncMock()
    mock_get_response = {
        "id": "1234-5678-90ab-cdef",
        "rule_id": "test-rule-id",
        "name": "Test Rule",
        "enabled": True
    }
    mock_patch_response = {
        "id": "1234-5678-90ab-cdef",
        "rule_id": "test-rule-id",
        "name": "Test Rule",
        "enabled": False
    }

    mock_client.get.return_value = create_mock_response(200, mock_get_response)
    mock_client.patch.return_value = create_mock_response(
        200, mock_patch_response)

    # Act
    result = await _call_update_rule_status(mock_client, rule_id="test-rule-id", enabled=False)

    # Assert
    assert "Successfully disabled rule" in result
    mock_client.get.assert_called_once()
    mock_client.patch.assert_called_once()

    # Verify the PATCH request contains the updated enabled field
    args, kwargs = mock_client.patch.call_args
    assert kwargs["json"]["enabled"] is False

# --- Tests for find_rules ---


@pytest.mark.asyncio
async def test_find_rules_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "data": [
            {
                "id": "rule-1",
                "name": "Rule 1",
                "enabled": True,
                "created_at": "2023-01-01T00:00:00.000Z"
            },
            {
                "id": "rule-2",
                "name": "Rule 2",
                "enabled": False,
                "created_at": "2023-01-02T00:00:00.000Z"
            }
        ],
        "page": 1,
        "perPage": 2,
        "total": 2
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_find_rules(mock_client)

    # Assert
    assert "Rule 1" in result
    assert "Rule 2" in result
    mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_find_rules_with_filter():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "data": [
            {
                "id": "rule-1",
                "name": "Rule 1",
                "enabled": True,
                "created_at": "2023-01-01T00:00:00.000Z"
            }
        ],
        "page": 1,
        "perPage": 1,
        "total": 1
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_find_rules(mock_client, filter="alert.attributes.name:\"Rule 1\"")

    # Assert
    assert "Rule 1" in result
    mock_client.get.assert_called_once()
    # Verify filter param was used
    args, kwargs = mock_client.get.call_args
    assert kwargs["params"]["filter"] == "alert.attributes.name:\"Rule 1\""

# --- Tests for get_prepackaged_rules_status ---


@pytest.mark.asyncio
async def test_get_prepackaged_rules_status_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "rules_custom_installed": 5,
        "rules_installed": 100,
        "rules_not_installed": 10,
        "rules_not_updated": 5,
        "timelines_installed": 20,
        "timelines_not_installed": 2,
        "timelines_not_updated": 1
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_prepackaged_rules_status(mock_client)

    # Assert
    assert "Prepackaged Detection Rules Status" in result
    assert "Custom rules installed: 5" in result
    assert "Prepackaged rules installed: 100" in result
    mock_client.get.assert_called_once()
    args, kwargs = mock_client.get.call_args
    assert args[0] == "/api/detection_engine/rules/prepackaged/_status"

# --- Tests for install_prepackaged_rules ---


@pytest.mark.asyncio
async def test_install_prepackaged_rules_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "rules_installed": 10,
        "rules_updated": 5,
        "timelines_installed": 2,
        "timelines_updated": 1
    }
    mock_client.put.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_install_prepackaged_rules(mock_client)

    # Assert
    assert "Prepackaged content installation completed successfully" in result
    assert "10 new rules installed" in result
    assert "5 existing rules updated" in result
    assert "2 new timelines installed" in result
    assert "1 existing timelines updated" in result
    mock_client.put.assert_called_once()
    args, kwargs = mock_client.put.call_args
    assert args[0] == "/api/detection_engine/rules/prepackaged"
