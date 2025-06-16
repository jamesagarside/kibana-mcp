import httpx
from typing import List, Optional, Dict, Callable, Awaitable
import mcp.types as types
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

# Helper function to execute tools safely
async def execute_tool_safely(
    tool_name: str,
    tool_impl_func: Callable[..., Awaitable[str]], # Type hint for the _call_... funcs
    http_client: httpx.AsyncClient,
    **kwargs
) -> list[types.TextContent]:
    """Wraps tool execution with client check, logging, and error handling."""
    if not http_client:
        tool_logger.error(f"HTTP client not initialized when attempting to call tool '{tool_name}'.")
        raise RuntimeError("HTTP client not initialized.")
    
    tool_logger.info(f"Executing tool '{tool_name}' with args: {kwargs}")
    try:
        # Pass the client and other args to the specific implementation
        result_text = await tool_impl_func(http_client=http_client, **kwargs)
        tool_logger.info(f"Tool '{tool_name}' executed successfully.")
        return [types.TextContent(type="text", text=str(result_text))]
    except TypeError as e:
        # Catch argument mismatches specifically
        tool_logger.error(f"Invalid arguments passed to tool '{tool_name}' implementation: {e}", exc_info=True)
        # Raise a more specific error if possible, or a generic one
        raise ValueError(f"Invalid arguments provided for tool '{tool_name}': {e}")
    except Exception as e:
        tool_logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        raise RuntimeError(f"An error occurred while executing tool '{tool_name}'.") 