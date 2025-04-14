import httpx
from typing import List, Optional, Dict
import json
import logging

tool_logger = logging.getLogger("kibana-mcp.tools")

async def _call_get_alerts(http_client: httpx.AsyncClient, limit: int, search_text: str) -> str:
    """Handles the API interaction for fetching alerts using Elasticsearch query DSL."""
    # Correct API endpoint for searching alert signals
    api_path = "/api/detection_engine/signals/search"

    # Construct the base Elasticsearch bool query
    bool_query: Dict = {
        "bool": {
            "must": [],
            "filter": [],
            "should": [],
            "must_not": []
        }
    }

    # If search_text is provided AND is not the default '*', add it as a multi_match filter
    if search_text != "*":
        # Place the multi_match query inside the 'filter' context for non-scoring search
        bool_query["bool"]["filter"].append({
            "multi_match": {
                "query": search_text,
                "fields": [
                    "kibana.alert.rule.name",
                    "kibana.alert.reason", # Added reason field
                    "signal.rule.name",    # Kept signal.rule.name just in case
                    "message",             # Kept message
                    "host.name",           # Kept host.name
                    "user.name",           # Kept user.name
                    "kibana.alert.rule.description", # Added description
                    "kibana.alert.uuid",   # Allow searching by alert UUID
                    "_id"                  # Allow searching by internal _id
                    # Add more fields as needed
                ]
            }
        })
    # If no search text, the bool query with empty clauses acts like match_all

    payload = {
        "query": bool_query, # Use the constructed bool query
        "size": limit,
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ]
        # Add other potential payload fields like aggregations, _source filtering etc. if needed
    }

    result_text = f"Attempting to fetch up to {limit} alerts (signals)"
    if search_text != "*":
        result_text += f" matching '{search_text}' using bool query"
    else:
        result_text += f" (matching all, as search_text is default '*')"
    result_text += "..."

    try:
        # Consider adding headers={"Elastic-Api-Version": "2023-10-31"} if needed
        response = await http_client.post(api_path, json=payload)
        response.raise_for_status()
        alerts_data = response.json()
        result_text = json.dumps(alerts_data, indent=2)

    except httpx.RequestError as exc:
        result_text += f"\nError calling Kibana API ({api_path}): {exc}"
    except httpx.HTTPStatusError as exc:
        result_text += f"\nKibana API ({api_path}) returned error: {exc.response.status_code} - {exc.response.text}"
    except json.JSONDecodeError:
         result_text += f"\nError parsing JSON response from Kibana API ({api_path})."
    except Exception as e:
         result_text += f"\nUnexpected error during alert signal fetch: {str(e)}"

    return result_text 