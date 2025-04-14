import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_get_rule_exceptions(http_client: httpx.AsyncClient, rule_id: str) -> str:
    """Handles the API interaction for retrieving exceptions associated with a rule."""
    # Assuming standard REST pattern: GET on the same endpoint used for POSTing items
    api_path = f"/api/detection_engine/rules/{rule_id}/exceptions"
    result_text = f"Attempting to retrieve exceptions for rule {rule_id}..."
    
    try:
        # Consider adding headers={"Elastic-Api-Version": "2023-10-31"} if needed
        response = await http_client.get(api_path)
        response.raise_for_status()
        exceptions_data = response.json()
        # Format the output for readability
        result_text = json.dumps(exceptions_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        # Handle 404 specifically - rule might not exist or have no exceptions/list
        if exc.response.status_code == 404:
             result_text += f"\\nKibana API ({api_path}) returned 404: Rule not found or no exception list associated."
        else:
             result_text += f"\\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
         result_text += f"\\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
         result_text += f"\\nUnexpected error retrieving rule exceptions: {str(e)}"
         
    return result_text 