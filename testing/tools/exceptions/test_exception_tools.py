import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the tools to test
from kibana_mcp.tools.exceptions.get_rule_exceptions import _call_get_rule_exceptions
from kibana_mcp.tools.exceptions.add_rule_exception_items import _call_add_rule_exception_items
from kibana_mcp.tools.exceptions.create_exception_list import _call_create_exception_list
from kibana_mcp.tools.exceptions.associate_shared_exception_list import _call_associate_shared_exception_list

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response

# --- Tests for get_rule_exceptions ---


@pytest.mark.asyncio
async def test_get_rule_exceptions_success():
    # Arrange
    mock_client = AsyncMock()

    # First, mock the GET request to get the rule details
    rule_response_data = {
        "id": "rule-uuid-123",
        "rule_id": "test-rule-id",
        "name": "Test Rule"
    }

    # Then, mock the GET request to get the rule exceptions
    exceptions_response_data = {
        "data": [
            {
                "id": "exception-1",
                "name": "Exception 1",
                "description": "Test exception 1"
            },
            {
                "id": "exception-2",
                "name": "Exception 2",
                "description": "Test exception 2"
            }
        ],
        "page": 1,
        "perPage": 2,
        "total": 2
    }

    # Set up the sequence of responses
    mock_client.get.side_effect = [
        create_mock_response(200, rule_response_data),
        create_mock_response(200, exceptions_response_data)
    ]

    # Act
    result = await _call_get_rule_exceptions(mock_client, rule_id="test-rule-id")

    # Assert
    assert "Exception 1" in result
    assert "Exception 2" in result
    # Should have made 2 GET requests
    assert mock_client.get.call_count == 2
    # First call should be to get the rule by rule_id
    first_call_args = mock_client.get.call_args_list[0]
    assert "rule_id=test-rule-id" in str(first_call_args)
    # Second call should be to get the exceptions using the internal rule UUID
    second_call_args = mock_client.get.call_args_list[1]
    assert "rule-uuid-123" in str(second_call_args)

# --- Tests for add_rule_exception_items ---


@pytest.mark.asyncio
async def test_add_rule_exception_items_success():
    # Arrange
    mock_client = AsyncMock()
    # First, mock the GET request to get the rule details
    rule_response_data = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "rule_id": "test-rule-id",
        "name": "Test Rule"
    }

    # Then, mock the POST request to add exception items
    add_exceptions_response_data = {
        "success": True,
        "exception_items": [
            {
                "id": "new-exception-1",
                "name": "New Exception"
            }
        ]
    }

    # Set up the sequence of responses
    mock_client.get.return_value = create_mock_response(
        200, rule_response_data)
    mock_client.post.return_value = create_mock_response(
        200, add_exceptions_response_data)

    # Create exception items to add
    exception_items = [
        {
            "name": "New Exception",
            "type": "simple",
            "entries": [
                {
                    "field": "source.ip",
                    "operator": "included",
                    "type": "match",
                    "value": "192.168.1.1"
                }
            ],
            "description": "Test exception"
        }
    ]

    # Act
    result = await _call_add_rule_exception_items(mock_client, rule_id="123e4567-e89b-12d3-a456-426614174000", items=exception_items)

    # Assert
    assert "Successfully added" in result
    assert "New Exception" in result
    # Should have made GET request for rule and POST for exceptions
    mock_client.get.assert_called_once()
    mock_client.post.assert_called_once()

# --- Tests for create_exception_list ---


@pytest.mark.asyncio
async def test_create_exception_list_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "exception-list-1",
        "list_id": "test-exceptions",
        "name": "Test Exceptions List"
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_create_exception_list(
        mock_client,
        list_id="test-exceptions",
        name="Test Exceptions List",
        description="List for test exceptions",
        type="detection"
    )

    # Assert
    assert "Successfully created" in result
    assert "Test Exceptions List" in result
    mock_client.post.assert_called_once()

    # Verify payload structure
    args, kwargs = mock_client.post.call_args
    assert kwargs["json"]["list_id"] == "test-exceptions"
    assert kwargs["json"]["name"] == "Test Exceptions List"

# --- Tests for associate_shared_exception_list ---


@pytest.mark.asyncio
async def test_associate_shared_exception_list_success():
    # Arrange
    mock_client = AsyncMock()
    # Mock data for the exception list GET request
    exception_list_response_data = {
        "id": "exception-list-id-1",
        "list_id": "shared-exception-list",
        "type": "detection",
        "namespace_type": "single"
    }

    # Mock data for the rule details GET request
    rule_response_data = {
        "id": "rule-uuid-123",
        "rule_id": "test-rule-id",
        "name": "Test Rule",
        "exceptions_list": []  # Initially no exceptions
    }

    # Then, mock the PATCH request to update rule with exception list
    updated_rule_response_data = {
        "id": "rule-uuid-123",
        "rule_id": "test-rule-id",
        "name": "Test Rule",
        "exceptions_list": [
            {
                "id": "exception-list-id-1",
                "list_id": "shared-exception-list",
                "type": "detection",
                "namespace_type": "single"
            }
        ]
    }

    # Set up the mock to return different responses for each call
    mock_responses = [
        create_mock_response(200, exception_list_response_data),
        create_mock_response(200, rule_response_data)
    ]
    mock_client.get.side_effect = mock_responses
    mock_client.patch.return_value = create_mock_response(
        200, updated_rule_response_data)

    # Act
    result = await _call_associate_shared_exception_list(
        mock_client,
        rule_id="test-rule-id",
        exception_list_id="shared-exception-list"
    )

    # Assert
    assert "Successfully associated" in result
    assert "shared-exception-list" in result
    assert "Test Rule" in result
    # Should have made two GET requests (one for the exception list, one for the rule)
    assert mock_client.get.call_count == 2
    mock_client.patch.assert_called_once()
