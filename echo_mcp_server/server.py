# echo_mcp_server/server.py
import asyncio
import logging
from fastmcp import FastMCP
import mcp.types as types # Import types for potential future use

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("echo-mcp")

logger.info("Initializing Echo MCP Server (FastMCP)...")
mcp = FastMCP("Echo")

@mcp.resource("echo://{message}")
async def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    logger.info(f"Handling echo_resource for: {message}")
    # Returning simple string as per example
    return f"Resource echo: {message}"

@mcp.tool()
async def echo_tool(message: str) -> list[types.TextContent]:
    """Echo a message as a tool"""
    logger.info(f"Handling echo_tool with message: {message}")
    # Return type should be list of content parts
    return [types.TextContent(type="text", text=f"Tool echo: {message}")]

# NOTE: The SDK example for @mcp.prompt just returned a string.
# A compliant get_prompt usually returns types.GetPromptResult.
# We'll implement a simple version returning a string for now, matching the SDK example closely.
@mcp.prompt("echo://{message}")
async def echo_prompt(message: str) -> str:
    """Create an echo prompt (simple version based on SDK example)"""
    logger.info(f"Handling echo_prompt for: {message}")
    return f"Please process this message: {message}"

# Allows running the server directly using `python echo_mcp_server/server.py`
if __name__ == "__main__":
    logger.info("Starting Echo MCP server run loop...")
    try:
        mcp.run() # Call synchronous run, which handles the event loop
        logger.info("Echo MCP server run loop finished normally.")
    except Exception as e:
        logger.error(f"Error during server run: {e}", exc_info=True)
        # Ensure script exits with error code if run fails
        import sys
        sys.exit(1) 