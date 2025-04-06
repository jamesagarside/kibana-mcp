import sys
import time
# Print to stdout first
print('{"message": "Test script started - stdout"}', flush=True)
print('{"message": "--- test_mcp.py starting --- "}', file=sys.stderr, flush=True)
time.sleep(5) # Keep it alive for a few seconds
print('{"message": "--- test_mcp.py finished --- "}', file=sys.stderr, flush=True)
sys.exit(0) 