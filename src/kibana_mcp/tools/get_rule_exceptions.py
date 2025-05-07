import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_get_rule_exceptions(http_client: httpx.AsyncClient, rule_id: str) -> str:
    """Handles the API interaction for retrieving exceptions associated with a rule.
    
    Now accepts the human-readable rule_id and automatically looks up the internal UUID.
    """
    result_text = f"Attempting to retrieve exceptions for rule with rule_id '{rule_id}'..."
    
    # First, look up the internal UUID using the rule_id
    get_rule_api_path = f"/api/detection_engine/rules?rule_id={rule_id}"
    
    try:
        # 1. Get the rule configuration to find the internal UUID
        result_text += f"\nFetching rule configuration from {get_rule_api_path}..."
        get_rule_response = await http_client.get(get_rule_api_path)
        get_rule_response.raise_for_status()
        rule_config = get_rule_response.json()
        
        # Extract internal ID (UUID)
        rule_internal_id = rule_config.get("id")
        if not rule_internal_id:
            result_text += "\nError: Could not extract internal 'id' (UUID) from fetched rule configuration."
            result_text += f"\nResponse: {json.dumps(rule_config, indent=2)}"
            return result_text
            
        result_text += f"\nSuccessfully fetched rule configuration. Internal UUID: {rule_internal_id}"
        
        # 2. Now use the internal UUID to get exceptions
        api_path = f"/api/detection_engine/rules/{rule_internal_id}/exceptions"
        result_text += f"\nUsing endpoint {api_path} with internal UUID..."
        
        # Consider adding headers={"Elastic-Api-Version": "2023-10-31"} if needed
        response = await http_client.get(api_path)
        response.raise_for_status()
        exceptions_data = response.json()
        # Format the output for readability
        result_text = f"Exceptions for rule '{rule_id}' (internal UUID: '{rule_internal_id}'):\n{json.dumps(exceptions_data, indent=2)}"

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API: {exc}"
    except httpx.HTTPStatusError as exc:
        # Provide more context based on which request failed
        if get_rule_api_path in exc.request.url.path:
            failed_op = "fetching rule"
        else:
            failed_op = "retrieving exceptions"
            # Handle 404 specifically - rule might not exist or have no exceptions/list
            if exc.response.status_code == 404:
                result_text += f"\nKibana API returned 404: Rule not found or no exception list associated."
                return result_text
                
        result_text += f"\nKibana API error during {failed_op}: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError as exc:
        result_text += f"\nError parsing JSON response from Kibana API: {exc}"
    except Exception as e:
        result_text += f"\nUnexpected error retrieving rule exceptions: {str(e)}"
         
    return result_text
