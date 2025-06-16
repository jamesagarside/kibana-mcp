import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the tools to test
from kibana_mcp.tools.alerts.get_alerts import _call_get_alerts
from kibana_mcp.tools.alerts.tag_alert import _call_tag_alert
from kibana_mcp.tools.alerts.adjust_alert_status import _call_adjust_alert_status

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response

# --- Tests for get_alerts ---


@pytest.mark.asyncio
async def test_get_alerts_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "hits": {
            "hits": [
                {
                    "_id": "alert-1",
                    "_source": {
                        "kibana.alert.rule.name": "Test Rule 1",
                        "kibana.alert.reason": "Test Reason 1"
                    }
                },
                {
                    "_id": "alert-2",
                    "_source": {
                        "kibana.alert.rule.name": "Test Rule 2",
                        "kibana.alert.reason": "Test Reason 2"
                    }
                }
            ],
            "total": {
                "value": 2,
                "relation": "eq"
            }
        }
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_alerts(mock_client, limit=10, search_text="*")

    # Assert
    # The function returns raw JSON, so we should test for the presence of the data
    assert "hits" in result
    assert "alert-1" in result
    assert "alert-2" in result
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_alerts_with_search():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "hits": {
            "hits": [
                {
                    "_id": "alert-1",
                    "_source": {
                        "kibana.alert.rule.name": "Test Rule 1",
                        "kibana.alert.reason": "Test Reason 1"
                    }
                }
            ],
            "total": {
                "value": 1,
                "relation": "eq"
            }
        }
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_alerts(mock_client, limit=10, search_text="Test Rule 1")

    # Assert
    assert "alert-1" in result
    mock_client.post.assert_called_once()
    # Verify search_text was used in the request
    args, kwargs = mock_client.post.call_args
    assert "Test Rule 1" in str(kwargs["json"])

# --- Tests for tag_alert ---


@pytest.mark.asyncio
async def test_tag_alert_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {"updated": 1}
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)
    tags_to_add = ["urgent", "suspicious"]

    # Act
    result = await _call_tag_alert(mock_client, alert_id="alert-123", tags_to_add=tags_to_add)

    # Assert
    assert "add tags" in result.lower()
    assert "Updated: 1" in result
    mock_client.post.assert_called_once()

    # Verify payload structure
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/detection_engine/signals/tags"
    assert kwargs["json"]["ids"] == ["alert-123"]
    assert kwargs["json"]["tags"]["tags_to_add"] == tags_to_add

# --- Tests for adjust_alert_status ---


@pytest.mark.asyncio
async def test_adjust_alert_status_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {"updated": 1}
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_adjust_alert_status(mock_client, alert_id="alert-123", new_status="acknowledged")

    # Assert
    assert "change status" in result.lower()
    assert "Successfully updated status for 1 signal" in result
    mock_client.post.assert_called_once()

    # Verify payload structure
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/detection_engine/signals/status"
    assert kwargs["json"]["signal_ids"] == ["alert-123"]
    assert kwargs["json"]["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_adjust_alert_status_invalid_status():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await _call_adjust_alert_status(mock_client, alert_id="alert-123", new_status="invalid_status")

    # Assert
    assert "Error: Invalid status" in result
    mock_client.post.assert_not_called()
