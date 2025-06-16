import httpx
from unittest.mock import MagicMock


def create_mock_response(status_code, json_data):
    """Helper function for creating mock responses in tests"""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = MagicMock()
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
    return mock_response
