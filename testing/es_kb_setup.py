import requests

# Use relative imports
from .utils import print_info, print_error, print_warning

# ==============================================================================
# --- Elasticsearch / Kibana Service & Setup Management ---
# ==============================================================================


def create_index_template(es_base_url, es_auth):
    """Creates an index template for mcp-auth-logs-* ensuring correct mappings."""
    template_name = "mcp_auth_logs_template"
    url = f"{es_base_url}/_index_template/{template_name}"
    print_info(f"Creating/updating index template: {template_name}...")

    template_payload = {
        "index_patterns": ["mcp-auth-logs-*"],
        "template": {
            "settings": {
                "index.number_of_shards": 1,
                "index.number_of_replicas": 0  # Suitable for single-node test cluster
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "source": {
                        "properties": {
                            "ip": {"type": "ip"}  # Map source.ip as IP type
                        }
                    },
                    "event": {
                        "properties": {
                            "action": {"type": "keyword"},
                            "outcome": {"type": "keyword"}
                        }
                    },
                    "user": {
                        "properties": {
                            "name": {"type": "keyword"}
                        }
                    },
                    # Keep message as text if present
                    "message": {"type": "text"}
                    # Add other field mappings as needed
                }
            }
        },
        "priority": 500  # High priority to override default dynamic mappings
    }

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.put(url, auth=es_auth, headers=headers,
                                json=template_payload, verify=False, timeout=10)
        if 200 <= response.status_code < 300:
            print_info(
                f"Index template '{template_name}' created/updated successfully.")
            return True
        else:
            print_warning(
                f"Failed to create/update index template '{template_name}' (HTTP {response.status_code}): {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(
            f"Error creating/updating index template '{template_name}': {e}")
        return False
