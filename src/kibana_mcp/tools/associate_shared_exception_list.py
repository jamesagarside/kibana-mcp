import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

# Renamed function
async def _call_associate_shared_exception_list(
    http_client: httpx.AsyncClient,
    rule_id: str,             # The human-readable rule_id
    exception_list_id: str, # The list_id of the shared exception list to associate
    exception_list_type: str = 'detection', # Type of the list (e.g., detection, endpoint)
    exception_list_namespace: str = 'single' # Namespace type ('single' or 'agnostic')
) -> str:
    """Associates an existing shared exception list with a detection rule using PATCH."""
    result_text = f"Attempting to associate shared exception list '{exception_list_id}' with rule '{rule_id}'..."
    get_rule_api_path = f"/api/detection_engine/rules?rule_id={rule_id}" 
    get_list_api_path = f"/api/exception_lists" # Endpoint for getting list details
    patch_rule_api_path = "/api/detection_engine/rules" # PATCH endpoint
    
    try:
        # 0. Fetch Exception List details to get its internal UUID
        result_text += f"\\nFetching details for exception list '{exception_list_id}' from {get_list_api_path}..."
 
        # Fetch the specific list using the list_id query parameter
        list_params = {"list_id": exception_list_id, "namespace_type": exception_list_namespace}
        get_list_response = await http_client.get(get_list_api_path, params=list_params)
        get_list_response.raise_for_status() # Raise HTTP errors (like 404)
 
        # The response should be the list object directly
        found_list = get_list_response.json()
        
        if not found_list:
            result_text += f"\\nError: Could not find exception list with list_id '{exception_list_id}' and type '{exception_list_type}'."
            return result_text

        exception_list_internal_id = found_list.get('id')
        if not exception_list_internal_id:
            result_text += f"\\nError: Found exception list '{exception_list_id}' but it is missing internal 'id' (UUID)."
            return result_text
        result_text += f"\\nFound exception list '{exception_list_id}' with internal ID '{exception_list_internal_id}'."

        # 1. Get current rule configuration
        result_text += f"\\nFetching current rule configuration from {get_rule_api_path}..."
        get_rule_response = await http_client.get(get_rule_api_path)
        get_rule_response.raise_for_status()
        rule_config = get_rule_response.json()
        
        # Extract internal ID (UUID)
        rule_internal_id = rule_config.get("id")
        if not rule_internal_id:
            result_text += "\\nError: Could not extract internal 'id' (UUID) from fetched rule configuration."
            result_text += f"\\nResponse: {json.dumps(rule_config, indent=2)}"
            return result_text
            
        result_text += "\\nSuccessfully fetched rule configuration."
            
        # 2. Modify the exceptions_list
        exceptions_list = rule_config.get("exceptions_list", [])
        
        # Check if the list is already present using the internal ID
        list_already_present = any(
            item.get("id") == exception_list_internal_id # Check by internal list ID
            for item in exceptions_list
        )

        if list_already_present:
            result_text += f"\\nException list with internal ID '{exception_list_internal_id}' ('{exception_list_type}') is already associated with rule '{rule_id}'. No update needed."
            return result_text
        
        # Add the new exception list reference using correct IDs
        new_exception_ref = {
            "id": exception_list_internal_id, # Use the fetched internal UUID
            "list_id": exception_list_id,     # Use the human-readable ID
            "type": exception_list_type,
            "namespace_type": exception_list_namespace
        }
        exceptions_list.append(new_exception_ref)
        # No need to assign back to rule_config["exceptions_list"] here, 
        # we only need the final list for the PATCH payload.

        result_text += f"\\nConstructed new exceptions_list for PATCH payload."

        # 3. Construct PATCH payload
        patch_payload = {
            "id": rule_internal_id, # Identify rule by internal ID
            # "version": rule_version, # Removed version handling
            "exceptions_list": exceptions_list # Provide the full updated list
        }

        result_text += f"\\nUpdating rule with PATCH request to {patch_rule_api_path}..."

        # 4. Send PATCH request
        patch_response = await http_client.patch(patch_rule_api_path, json=patch_payload)
        patch_response.raise_for_status()
        updated_rule_data = patch_response.json()
        result_text += f"\\nSuccessfully associated shared exception list '{exception_list_id}' with rule '{rule_id}' (internal ID: '{rule_internal_id}')."
        result_text += f"\\nUpdate Response:\\n{json.dumps(updated_rule_data, indent=2)}"

    except httpx.RequestError as exc:
        result_text += f"\\nError calling Kibana API: {exc}"
    except httpx.HTTPStatusError as exc:
        # Provide more context based on which request failed
        failed_op = "fetching shared list" if get_list_api_path in exc.request.url.path else "fetching rule" if get_rule_api_path in exc.request.url.path else "updating rule"
        result_text += f"\\nKibana API error during {failed_op}: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError as exc:
        result_text += f"\\nError parsing JSON response from Kibana API: {exc}"
    except Exception as e:
        result_text += f"\\nUnexpected error associating shared exception list with rule: {str(e)}"
        
    return result_text
