from . import server
import asyncio
import sys

def main():
    """Entry point function to start the server."""
    asyncio.run(server.run_server())

# Optionally expose other important items at package level
__all__ = ['main', 'server']