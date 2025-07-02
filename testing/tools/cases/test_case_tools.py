import pytest
import httpx
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the tools to test
from kibana_mcp.tools.cases.find_cases import _call_find_cases
from kibana_mcp.tools.cases.get_case import _call_get_case
from kibana_mcp.tools.cases.create_case import _call_create_case
from kibana_mcp.tools.cases.update_case import _call_update_case
from kibana_mcp.tools.cases.delete_cases import _call_delete_cases
from kibana_mcp.tools.cases.add_case_comment import _call_add_case_comment
from kibana_mcp.tools.cases.get_case_comments import _call_get_case_comments
from kibana_mcp.tools.cases.get_case_alerts import _call_get_case_alerts
from kibana_mcp.tools.cases.get_cases_by_alert import _call_get_cases_by_alert
from kibana_mcp.tools.cases.get_case_configuration import _call_get_case_configuration
from kibana_mcp.tools.cases.get_case_tags import _call_get_case_tags

# Import test utilities
from testing.tools.utils.test_utils import create_mock_response

# --- Tests for find_cases ---


@pytest.mark.asyncio
async def test_find_cases_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "cases": [
            {
                "id": "case-1",
                "title": "Test Case 1",
                "description": "Test Description 1",
                "status": "open",
                "severity": "medium",
                "created_at": "2023-01-01T00:00:00.000Z",
                "tags": ["tag1", "tag2"]
            },
            {
                "id": "case-2",
                "title": "Test Case 2",
                "description": "Test Description 2",
                "status": "closed",
                "severity": "high",
                "created_at": "2023-01-02T00:00:00.000Z",
                "tags": ["tag3"]
            }
        ],
        "total": 2,
        "page": 1,
        "per_page": 20,
        "count_open_cases": 1,
        "count_closed_cases": 1,
        "count_in_progress_cases": 0
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_find_cases(mock_client, page=1, per_page=20)

    # Assert
    assert "Test Case 1" in result
    assert "Test Case 2" in result
    assert '"total": 2' in result
    mock_client.get.assert_called_once_with("/api/cases/_find", params={
        "page": 1,
        "perPage": 20,
        "sortField": "created_at",
        "sortOrder": "desc",
        "defaultSearchOperator": "OR"
    })


@pytest.mark.asyncio
async def test_find_cases_with_filters():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {"cases": [], "total": 0}
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_find_cases(
        mock_client,
        status="open",
        severity="high",
        tags=["urgent", "security"],
        search="malware"
    )

    # Assert
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert call_args[0][0] == "/api/cases/_find"
    params = call_args[1]["params"]
    assert params["status"] == "open"
    assert params["severity"] == "high"
    assert params["tags"] == ["urgent", "security"]
    assert params["search"] == "malware"


@pytest.mark.asyncio
async def test_find_cases_http_error():
    # Arrange
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=MagicMock(status_code=404, text="Not Found")
    )

    # Act
    result = await _call_find_cases(mock_client)

    # Assert
    assert "returned error: 404" in result
    assert "Not Found" in result


# --- Tests for get_case ---


@pytest.mark.asyncio
async def test_get_case_success():
    # Arrange
    mock_client = AsyncMock()
    case_id = "test-case-id"
    mock_response_data = {
        "id": case_id,
        "title": "Sample Case",
        "description": "Sample case description",
        "status": "open",
        "severity": "medium",
        "created_at": "2023-01-01T00:00:00.000Z",
        "tags": ["security", "investigation"],
        "comments": []
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_case(mock_client, case_id)

    # Assert
    assert "Sample Case" in result
    assert case_id in result
    assert '"status": "open"' in result
    mock_client.get.assert_called_once_with(f"/api/cases/{case_id}")


@pytest.mark.asyncio
async def test_get_case_not_found():
    # Arrange
    mock_client = AsyncMock()
    case_id = "nonexistent-case"
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=MagicMock(status_code=404, text="Case not found")
    )

    # Act
    result = await _call_get_case(mock_client, case_id)

    # Assert
    assert "returned error: 404" in result
    assert "Case not found" in result


# --- Tests for create_case ---


@pytest.mark.asyncio
async def test_create_case_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "new-case-id",
        "title": "New Security Case",
        "description": "Description of the security incident",
        "status": "open",
        "severity": "high",
        "created_at": "2023-01-01T00:00:00.000Z",
        "tags": ["security", "urgent"],
        "owner": "securitySolution"
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_create_case(
        mock_client,
        title="New Security Case",
        description="Description of the security incident",
        tags=["security", "urgent"],
        severity="high"
    )

    # Assert
    assert "New Security Case" in result
    assert "new-case-id" in result
    assert '"status": "open"' in result
    mock_client.post.assert_called_once()

    # Check the payload
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "/api/cases"
    payload = call_args[1]["json"]
    assert payload["title"] == "New Security Case"
    assert payload["description"] == "Description of the security incident"
    assert payload["tags"] == ["security", "urgent"]
    assert payload["severity"] == "high"


@pytest.mark.asyncio
async def test_create_case_minimal():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = {
        "id": "minimal-case-id",
        "title": "Minimal Case",
        "description": "Basic case",
        "status": "open",
        "severity": "low"
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_create_case(
        mock_client,
        title="Minimal Case",
        description="Basic case"
    )

    # Assert
    assert "Minimal Case" in result
    mock_client.post.assert_called_once()


# --- Tests for update_case ---


@pytest.mark.asyncio
async def test_update_case_success():
    # Arrange
    mock_client = AsyncMock()
    case_id = "test-case-id"
    version = "WzAsMV0="
    mock_response_data = [{
        "id": case_id,
        "title": "Updated Case Title",
        "description": "Updated description",
        "status": "in-progress",
        "severity": "high",
        "version": "WzEsMV0="
    }]
    mock_client.patch.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_update_case(
        mock_client,
        case_id=case_id,
        version=version,
        title="Updated Case Title",
        status="in-progress",
        severity="high"
    )

    # Assert
    assert "Updated Case Title" in result
    assert '"status": "in-progress"' in result
    mock_client.patch.assert_called_once()

    # Check the payload
    call_args = mock_client.patch.call_args
    assert call_args[0][0] == "/api/cases"
    payload = call_args[1]["json"]
    assert payload["cases"][0]["id"] == case_id
    assert payload["cases"][0]["version"] == version
    assert payload["cases"][0]["title"] == "Updated Case Title"
    assert payload["cases"][0]["status"] == "in-progress"


# --- Tests for delete_cases ---


@pytest.mark.asyncio
async def test_delete_cases_success():
    # Arrange
    mock_client = AsyncMock()
    case_ids = ["case-1", "case-2"]
    # Mock 204 No Content response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.raise_for_status.return_value = None
    mock_client.delete.return_value = mock_response

    # Act
    result = await _call_delete_cases(mock_client, case_ids)

    # Assert
    assert "Successfully deleted 2 case(s)" in result
    assert "case-1" in result
    assert "case-2" in result
    mock_client.delete.assert_called_once_with(
        "/api/cases", params={"ids": case_ids})


# --- Tests for add_case_comment ---


@pytest.mark.asyncio
async def test_add_case_comment_user_success():
    # Arrange
    mock_client = AsyncMock()
    case_id = "test-case-id"
    mock_response_data = {
        "id": case_id,
        "comments": [{
            "id": "comment-id",
            "type": "user",
            "comment": "This is a test comment",
            "created_at": "2023-01-01T00:00:00.000Z"
        }]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_add_case_comment(
        mock_client,
        case_id=case_id,
        comment_type="user",
        comment="This is a test comment"
    )

    # Assert
    assert "This is a test comment" in result
    mock_client.post.assert_called_once()

    call_args = mock_client.post.call_args
    assert call_args[0][0] == f"/api/cases/{case_id}/comments"
    payload = call_args[1]["json"]
    assert payload["type"] == "user"
    assert payload["comment"] == "This is a test comment"


@pytest.mark.asyncio
async def test_add_case_comment_alert_success():
    # Arrange
    mock_client = AsyncMock()
    case_id = "test-case-id"
    mock_response_data = {
        "id": case_id,
        "comments": [{
            "id": "comment-id",
            "type": "alert",
            "alertId": ["alert-1", "alert-2"],
            "index": ".alerts-security.alerts-default"
        }]
    }
    mock_client.post.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_add_case_comment(
        mock_client,
        case_id=case_id,
        comment_type="alert",
        alert_ids=["alert-1", "alert-2"],
        alert_index=".alerts-security.alerts-default"
    )

    # Assert
    assert "alert-1" in result
    assert "alert-2" in result
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_add_case_comment_invalid_type():
    # Arrange
    mock_client = AsyncMock()
    case_id = "test-case-id"

    # Act
    result = await _call_add_case_comment(
        mock_client,
        case_id=case_id,
        comment_type="invalid"
    )

    # Assert
    assert "Invalid comment type 'invalid'" in result
    mock_client.post.assert_not_called()


# --- Tests for get_case_comments ---


@pytest.mark.asyncio
async def test_get_case_comments_success():
    # Arrange
    mock_client = AsyncMock()
    case_id = "test-case-id"
    mock_response_data = {
        "comments": [
            {
                "id": "comment-1",
                "type": "user",
                "comment": "First comment",
                "created_at": "2023-01-01T00:00:00.000Z"
            },
            {
                "id": "comment-2",
                "type": "user",
                "comment": "Second comment",
                "created_at": "2023-01-02T00:00:00.000Z"
            }
        ],
        "page": 1,
        "per_page": 20,
        "total": 2
    }
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_case_comments(mock_client, case_id)

    # Assert
    assert "First comment" in result
    assert "Second comment" in result
    assert '"total": 2' in result
    mock_client.get.assert_called_once_with(
        f"/api/cases/{case_id}/comments/_find",
        params={"page": 1, "perPage": 20, "sortOrder": "desc"}
    )


# --- Tests for get_case_alerts ---


@pytest.mark.asyncio
async def test_get_case_alerts_success():
    # Arrange
    mock_client = AsyncMock()
    case_id = "test-case-id"
    mock_response_data = [
        {
            "id": "alert-1",
            "index": ".alerts-security.alerts-default",
            "rule": {
                "id": "rule-1",
                "name": "Test Rule"
            }
        }
    ]
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_case_alerts(mock_client, case_id)

    # Assert
    assert "alert-1" in result
    assert "Test Rule" in result
    mock_client.get.assert_called_once_with(f"/api/cases/{case_id}/alerts")


# --- Tests for get_cases_by_alert ---


@pytest.mark.asyncio
async def test_get_cases_by_alert_success():
    # Arrange
    mock_client = AsyncMock()
    alert_id = "test-alert-id"
    mock_response_data = [
        {
            "id": "case-1",
            "title": "Case containing alert"
        },
        {
            "id": "case-2",
            "title": "Another case with alert"
        }
    ]
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_cases_by_alert(mock_client, alert_id)

    # Assert
    assert "Case containing alert" in result
    assert "Another case with alert" in result
    mock_client.get.assert_called_once_with(
        f"/api/cases/alerts/{alert_id}", params={})


# --- Tests for get_case_configuration ---


@pytest.mark.asyncio
async def test_get_case_configuration_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = [{
        "id": "config-1",
        "closure_type": "close-by-user",
        "connector": {
            "id": "none",
            "name": "none",
            "type": ".none"
        },
        "owner": "securitySolution"
    }]
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_case_configuration(mock_client)

    # Assert
    assert "config-1" in result
    assert "close-by-user" in result
    assert "securitySolution" in result
    mock_client.get.assert_called_once_with("/api/cases/configure", params={})


# --- Tests for get_case_tags ---


@pytest.mark.asyncio
async def test_get_case_tags_success():
    # Arrange
    mock_client = AsyncMock()
    mock_response_data = ["security", "investigation", "malware", "urgent"]
    mock_client.get.return_value = create_mock_response(
        200, mock_response_data)

    # Act
    result = await _call_get_case_tags(mock_client)

    # Assert
    assert "security" in result
    assert "investigation" in result
    assert "malware" in result
    assert "urgent" in result
    mock_client.get.assert_called_once_with("/api/cases/tags", params={})
