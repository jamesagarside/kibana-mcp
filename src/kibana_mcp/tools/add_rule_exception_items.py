import httpx
from typing import List, Optional, Dict
import json
import logging
from pydantic import ValidationError

from kibana_mcp.models.exception_models import AddRuleExceptionItemsRequest, ExceptionItem

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_add_rule_exception_items(http_client: httpx.AsyncClient, rule_id: str, items: List[Dict]) -> str:
    """Handles the API interaction for adding exception items to a rule's list.
    
    Now accepts the human-readable rule_id and automatically looks up the internal UUID.
    Uses Pydantic models for input validation.
    """
    # Validate input using Pydantic models
    try:
        # Create the request model
        request = AddRuleExceptionItemsRequest(rule_id=rule_id, items=[ExceptionItem.model_validate(item) for item in items])
        # Validation passed
        result_text = f"Validated and attempting to add {len(request.items)} exception item(s) to rule with rule_id '{request.rule_id}'..."
    except ValidationError as e:
        return f"Input validation error: {str(e)}"
    
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
        
        # 2. Now use the internal UUID to add exceptions
        api_path = f"/api/detection_engine/rules/{rule_internal_id}/exceptions"
        result_text += f"\nUsing endpoint {api_path} with internal UUID..."
        
        # The payload structure requires the items under an "items" key
        # IMPORTANT: Based on trial-and-error, list_id should be omitted from the item dict
        # when using this endpoint, as the list is implied by the rule association.
        items_without_list_id = []
        for item in request.items:
            # Convert Pydantic model to dict and remove list_id if present
            item_dict = item.model_dump(exclude_none=True)
            if 'list_id' in item_dict:
                del item_dict['list_id']
            items_without_list_id.append(item_dict)

        payload = {"items": items_without_list_id}

        # Add the Elastic-Api-Version header as specified in the docs for POST
        headers = {"Elastic-Api-Version": "2023-10-31"}
        response = await http_client.post(api_path, json=payload, headers=headers)
        response.raise_for_status()
        # Response contains the created items with their IDs
        response_data = response.json()
        result_text += f"\nSuccessfully added items to rule '{rule_id}' (internal UUID: '{rule_internal_id}'). Response:\n{json.dumps(response_data, indent=2)}"

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API: {exc}"
    except httpx.HTTPStatusError as exc:
        # Provide more context based on which request failed
        failed_op = "fetching rule" if get_rule_api_path in exc.request.url.path else "adding exceptions"
        result_text += f"\nKibana API error during {failed_op}: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError as exc:
        result_text += f"\nError parsing JSON response from Kibana API: {exc}"
    except Exception as e:
        result_text += f"\nUnexpected error adding rule exception items: {str(e)}"
         
    return result_text
