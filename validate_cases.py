#!/usr/bin/env python3
"""
Quick validation test for the cases tools.
This tests that the tools can be imported and called without errors.
"""

import asyncio
import httpx
from unittest.mock import AsyncMock
import sys
import os

# Add the src directory to the path
sys.path.insert(0, 'src')


async def test_cases_tools():
    """Test that cases tools can be imported and called."""
    try:
        # Import cases tools
        from kibana_mcp.tools.cases.find_cases import _call_find_cases
        from kibana_mcp.tools.cases.get_case import _call_get_case
        from kibana_mcp.tools.cases.create_case import _call_create_case

        print("✅ Cases tools imported successfully")

        # Create a mock client
        mock_client = AsyncMock()

        # Mock a successful response for find_cases
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "cases": [{"id": "test-case", "title": "Test Case"}],
            "total": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response

        # Test find_cases
        result = await _call_find_cases(mock_client)
        print("✅ find_cases tool callable")

        # Test get_case
        result = await _call_get_case(mock_client, "test-case-id")
        print("✅ get_case tool callable")

        # Test create_case
        mock_client.post.return_value = mock_response
        result = await _call_create_case(
            mock_client,
            title="Test Case",
            description="Test Description"
        )
        print("✅ create_case tool callable")

        print("🎉 All cases tools validation passed!")
        return True

    except Exception as e:
        print(f"❌ Error during cases tools validation: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cases_tools())
    sys.exit(0 if success else 1)
