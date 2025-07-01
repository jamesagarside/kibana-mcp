#!/usr/bin/env python3
"""
Example demonstrating how to use the Kibana MCP SSE endpoint.

This example shows how to:
1. Connect to the SSE endpoint
2. Send MCP requests
3. Handle responses

Note: This requires the 'requests' package to be installed.
"""

import json
import time
import sys
from typing import Dict, Any


def make_mcp_request(tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create an MCP tool request."""
    return {
        "jsonrpc": "2.0",
        "id": f"req-{int(time.time() * 1000)}",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }


def example_usage():
    """Example usage of the SSE endpoint."""
    
    # This would be the actual SSE endpoint URL
    sse_url = "http://127.0.0.1:8000/sse"
    
    print("Kibana MCP SSE Endpoint Example")
    print("=" * 40)
    print()
    print(f"SSE Endpoint: {sse_url}")
    print()
    
    # Example requests
    examples = [
        {
            "name": "Get Alerts",
            "request": make_mcp_request("get_alerts", {"limit": 5})
        },
        {
            "name": "Find Rules", 
            "request": make_mcp_request("find_rules", {"per_page": 3})
        },
        {
            "name": "Get Alert by ID",
            "request": make_mcp_request("tag_alert", {
                "alert_id": "example-alert-id",
                "tags": ["example", "test"]
            })
        }
    ]
    
    print("Example MCP Requests:")
    print("-" * 20)
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print("Request JSON:")
        print(json.dumps(example['request'], indent=2))
        
        print("\nTo send this request to the SSE endpoint, you would:")
        print(f"  POST {sse_url}")
        print("  Content-Type: application/json")
        print("  Body: (the JSON above)")
        print()
    
    print("Note: Make sure to:")
    print("1. Set your Kibana credentials in environment variables")
    print("2. Start the SSE server with: make dev-sse")
    print("3. Use a proper SSE client library for production use")


def test_with_requests():
    """Test the SSE endpoint using requests library (if available)."""
    try:
        import requests
        
        sse_url = "http://127.0.0.1:8000/sse"
        
        # Test basic connectivity
        print("Testing SSE endpoint connectivity...")
        
        try:
            response = requests.get(sse_url, timeout=5)
            print(f"✅ SSE endpoint is reachable (status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to SSE endpoint. Is the server running?")
            print("   Start with: make dev-sse")
            return
        
        # Test MCP request
        print("\nTesting MCP request...")
        request_data = make_mcp_request("get_alerts", {"limit": 1})
        
        try:
            response = requests.post(
                sse_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                print("✅ MCP request successful!")
                # Note: In a real SSE implementation, this would be streamed
                print("Response preview:")
                print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            else:
                print(f"❌ MCP request failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error making MCP request: {e}")
            
    except ImportError:
        print("❌ 'requests' library not available.")
        print("   Install with: pip install requests")
        print("   Or use: uv add requests")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_with_requests()
    else:
        example_usage()
        print("\nTo test the endpoint, run:")
        print("  python example_sse_usage.py --test")
