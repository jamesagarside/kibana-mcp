import time
import json
import requests
import datetime
from pathlib import Path

# Use relative imports
from .utils import print_info, print_error, print_warning
from .config import (
    SAMPLE_RULE_FILE, MAX_ALERT_WAIT_SECONDS, ALERT_CHECK_INTERVAL_SECONDS
)

AUTH_EVENTS_FILE = Path(__file__).parent.resolve() / "auth_events.ndjson"

# ==============================================================================
# --- Detection Rule / Signal Management ---
# ==============================================================================
def create_sample_detection_rule(kibana_base_url, kibana_auth):
    """Creates a sample DETECTION rule using the Kibana API. Returns the rule ID on success, None otherwise."""
    url = f"{kibana_base_url}/api/detection_engine/rules"
    rule_name = None # Still useful for finding existing rule
    rule_id = None
    print_info("Attempting to create sample detection rule via Kibana API...")
    try:
        with open(SAMPLE_RULE_FILE, 'r') as f:
            rule_payload = json.load(f)
            rule_name = rule_payload.get("name") # Extract rule name for potential lookup

        if not rule_name:
            print_error("Rule name not found in sample_rule.json")
            return None

        headers = {
            "kbn-xsrf": "true",
            "Content-Type": "application/json"
        }
        response = requests.post(
            url,
            auth=kibana_auth,
            headers=headers,
            json=rule_payload,
            verify=False,
            timeout=15
        )

        if 200 <= response.status_code < 300:
            rule_data = response.json()
            rule_id = rule_data.get("id")
            print_info(f"Successfully created/updated sample detection rule '{rule_name}' (ID: {rule_id}) (HTTP {response.status_code}).")
            return rule_id # Return the actual rule ID
        elif response.status_code == 409:
            # If it already exists, we need to FIND its ID to return it
            print_info(f"Sample detection rule '{rule_name}' likely already exists (HTTP {response.status_code}). Attempting to find its ID...")
            find_url = f"{kibana_base_url}/api/detection_engine/rules/_find"
            # Filter needs to match the field structure for detection rules API
            find_params = {"filter": f'alert.attributes.name: "{rule_name}"'} # This filter might be wrong for detection rules, adjust if needed
            try:
                find_response = requests.get(find_url, auth=kibana_auth, headers=headers, params=find_params, verify=False, timeout=10)
                if find_response.status_code == 200:
                    find_data = find_response.json()
                    if find_data.get("data") and len(find_data["data"]) > 0:
                        found_rule_id = find_data["data"][0]["id"]
                        print_info(f"Found existing rule ID: {found_rule_id}")
                        return found_rule_id
                    else:
                        print_warning(f"Rule '{rule_name}' conflict reported, but could not find existing rule by name.")
                else:
                     print_warning(f"Failed to find existing rule by name (HTTP {find_response.status_code}): {find_response.text}")
            except Exception as find_e:
                 print_warning(f"Error trying to find existing rule ID: {find_e}")
            return None # Failed to get ID on conflict
        else:
            print_warning(f"Failed to create sample detection rule (HTTP {response.status_code}). Response: {response.text}")
            return None

    except FileNotFoundError:
        print_error(f"Sample rule file not found at {SAMPLE_RULE_FILE}")
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse sample rule file {SAMPLE_RULE_FILE}: {e}")
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to send request to create rule: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred creating the rule: {e}")
    return None # Return None on any error

def write_auth_data(es_base_url, es_auth):
    """Writes sample authentication events (from NDJSON file) to Elasticsearch."""
    if not AUTH_EVENTS_FILE.exists():
        print_error(f"Auth events file not found: {AUTH_EVENTS_FILE}")
        return False

    url = f"{es_base_url}/_bulk"
    # Use a data stream naming convention
    index_name = "mcp-auth-logs-default"
    print_info(f"Writing auth events from {AUTH_EVENTS_FILE.name} to Elasticsearch index '{index_name}'...")

    bulk_data = ""
    try:
        with open(AUTH_EVENTS_FILE, 'r') as f:
            for line in f:
                if not line.strip(): continue # Skip empty lines
                try:
                    doc = json.loads(line)
                    # Add timestamp and action metadata for bulk API
                    action_meta = json.dumps({"index": {"_index": index_name}})
                    doc["@timestamp"] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    bulk_data += action_meta + "\n" + json.dumps(doc) + "\n"
                except json.JSONDecodeError as e:
                    print_warning(f"Skipping invalid JSON line in {AUTH_EVENTS_FILE.name}: {line.strip()} - Error: {e}")

        if not bulk_data:
             print_warning(f"No valid data found in {AUTH_EVENTS_FILE.name}.")
             return False

        headers = {"Content-Type": "application/x-ndjson"}
        response = requests.post(
            url,
            auth=es_auth,
            headers=headers,
            data=bulk_data.encode('utf-8'),
            verify=False,
            timeout=15 # Increased timeout slightly for potentially larger bulk request
        )

        if response.status_code == 200:
            response_json = response.json()
            if response_json.get("errors"):
                # Find first error for better reporting
                first_error = "Unknown error" 
                try:
                    first_error = response_json["items"][0]["index"]["error"]["reason"]
                except (IndexError, KeyError, TypeError):
                    pass
                print_warning(f"Elasticsearch Bulk API reported errors. First error: {first_error}. Full response: {response_json}")
                return False
            else:
                item_count = len(response_json.get("items", []))
                print_info(f"Successfully wrote {item_count} auth event(s) to Elasticsearch.")
                return True
        else:
            print_warning(f"Failed to write auth events (HTTP {response.status_code}). Response: {response.text}")
            return False

    except FileNotFoundError: # Should be caught by initial check
        print_error(f"Auth events file not found: {AUTH_EVENTS_FILE}")
    except Exception as e:
        print_error(f"An unexpected error occurred writing auth events: {e}")

    return False

def wait_for_signals(kibana_base_url, kibana_auth, rule_id):
    """Waits for detection signals generated by the specified rule ID to appear."""
    if not rule_id:
        print_warning("Cannot wait for signals without a valid rule ID.")
        return False

    start_time = time.time()
    url = f"{kibana_base_url}/api/detection_engine/signals/search"
    print_info(f"Waiting up to {MAX_ALERT_WAIT_SECONDS}s for signals from rule ID '{rule_id}' to be generated...")

    search_payload = {
        "query": {
            "bool": {
                "filter": [
                    { "term": { "kibana.alert.rule.uuid": rule_id } }
                ]
            }
        },
        "size": 1,
        "sort": [{ "@timestamp": "desc" }]
    }

    headers = {
        "kbn-xsrf": "true",
        "Content-Type": "application/json"
    }

    while time.time() - start_time < MAX_ALERT_WAIT_SECONDS:
        try:
            response = requests.post(
                url,
                auth=kibana_auth,
                headers=headers,
                json=search_payload,
                verify=False,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                signal_count = data.get('hits', {}).get('total', {}).get('value', 0)
                if signal_count > 0:
                    print_info(f"Successfully found {signal_count} signal(s) generated by rule ID '{rule_id}'.")
                    return True
                else:
                    print_info(f"Found 0 signals from rule ID '{rule_id}' yet. Checking again in {ALERT_CHECK_INTERVAL_SECONDS}s...")
            elif response.status_code == 404:
                 print_info(f"Signals index likely not created yet (HTTP 404). Checking again in {ALERT_CHECK_INTERVAL_SECONDS}s...")
            else:
                print_warning(f"Signal search query failed (HTTP {response.status_code}). Response: {response.text}. Retrying...")

        except requests.exceptions.RequestException as e:
            print_warning(f"Error querying signals: {e}. Retrying...")
        except Exception as e:
            print_warning(f"Unexpected error querying signals: {e}. Retrying...")

        time.sleep(ALERT_CHECK_INTERVAL_SECONDS)

    print_error(f"Timed out after {MAX_ALERT_WAIT_SECONDS}s waiting for signals from rule ID '{rule_id}'.")
    return False 