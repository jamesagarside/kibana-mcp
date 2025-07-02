#!/usr/bin/env python3
"""
Minimal SSE Server Test

Just starts the server and verifies it's running.
"""

import os
import subprocess
import sys
import time
import socket


def test_port_open(host, port, timeout=5):
    """Test if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def main():
    """Test SSE server startup."""
    print("🧪 Minimal SSE Server Test")
    print("=" * 30)

    if not os.path.exists("src/kibana_mcp/server.py"):
        print("❌ Error: Run from kibana-mcp project root")
        return 1

    host = "127.0.0.1"
    port = 8000

    # Set up environment
    env = os.environ.copy()
    env.update({
        "MCP_TRANSPORT": "sse",
        "MCP_SSE_HOST": host,
        "MCP_SSE_PORT": str(port),
        "KIBANA_URL": "http://localhost:5601",
        "KIBANA_USERNAME": "test",
        "KIBANA_PASSWORD": "test"
    })

    print(f"🚀 Starting server on {host}:{port}...")

    # Start server
    process = subprocess.Popen(
        [sys.executable, "-m", "src.kibana_mcp.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )

    try:
        # Wait for server to start
        print("⏳ Waiting for server...")

        for i in range(30):  # 30 second timeout
            if test_port_open(host, port):
                print(f"✅ Server is listening on {host}:{port}")
                print(
                    f"🌐 SSE endpoint should be at: http://{host}:{port}/sse/")

                # Let it run for a few seconds
                print("⏱️  Letting server run for 5 seconds...")
                time.sleep(5)

                print("✅ Test completed successfully!")
                return 0

            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print("❌ Server process died:")
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
                return 1

            time.sleep(1)

        print("❌ Server didn't start within 30 seconds")
        return 1

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        return 1
    finally:
        print("🛑 Stopping server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    sys.exit(main())
