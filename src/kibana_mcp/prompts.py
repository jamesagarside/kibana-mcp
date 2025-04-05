import mcp.types as types

# Placeholder for accessing resource state if prompts depend on it
# from .resources import resource_state

async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts. (Stub implementation)
    """
    # Return an empty list or example prompts
    print("MCP Server: handle_list_prompts called (stub)")
    return []
    # Example:
    # return [
    #     types.Prompt(
    #         name="example-prompt",
    #         description="An example prompt definition",
    #         arguments=[]
    #     )
    # ]

async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt based on name and arguments. (Stub implementation)
    """
    # Raise an error or return placeholder content
    print(f"MCP Server: handle_get_prompt called for prompt '{name}' with args: {arguments} (stub)")
    raise ValueError(f"Prompt generation not implemented yet for: {name}") 