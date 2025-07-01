#!/usr/bin/env python3
"""
Simple test script to verify the Kibana MCP SSE server is running.
"""

import requests
import json

def test_sse_server(host="127.0.0.1", port=8000):
    """Test if the SSE server is responding."""
    base_url = f"http://{host}:{port}"
    
    print(f"Testing SSE server at {base_url}")
    
    try:
        # Test the SSE endpoint
        response = requests.get(f"{base_url}/sse", timeout=5)
        print(f"SSE endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SSE server is running and accessible!")
        else:
            print(f"❌ SSE server returned status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to SSE server. Make sure it's running.")
    except requests.exceptions.Timeout:
        print("❌ Connection to SSE server timed out.")
    except Exception as e:
        print(f"❌ Error testing SSE server: {e}")

if __name__ == "__main__":
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    test_sse_server(host, port)
