import time
import requests
import sys

# Assuming utils.py and config.py are in the same directory
from .utils import print_info, print_error, print_warning
from .config import (
    MAX_ES_WAIT_SECONDS, ES_CHECK_INTERVAL_SECONDS,
    MAX_KIBANA_WAIT_SECONDS, KIBANA_CHECK_INTERVAL_SECONDS,
    CUSTOM_KIBANA_ROLE_NAME, KIBANA_SYSTEM_USER, KIBANA_SYSTEM_PASSWORD,
    CUSTOM_KIBANA_ROLE_PAYLOAD
)

# ==============================================================================
# --- Elasticsearch / Kibana Service & Setup Management ---
# ==============================================================================
def wait_for_elasticsearch(es_base_url, es_auth):
    """Waits for the Elasticsearch root endpoint to return 200."""
    start_time = time.time()
    url = f"{es_base_url}/"
    print_info(f"Waiting for Elasticsearch API at {url}...")
    while time.time() - start_time < MAX_ES_WAIT_SECONDS:
        try:
            response = requests.get(url, auth=es_auth, verify=False, timeout=5)
            if response.status_code == 200:
                print_info(f"Elasticsearch API is up! (Status {response.status_code})")
                return True # Simple root check is likely enough for API readiness
            else:
                print_info(f"Elasticsearch API not ready yet (Status: {response.status_code}). Retrying...")
        except requests.exceptions.ConnectionError:
            print_info("Elasticsearch API connection refused. Retrying...")
        except requests.exceptions.Timeout:
            print_info("Elasticsearch API connection timed out. Retrying...")
        except Exception as e:
            print_warning(f"Error checking Elasticsearch status: {e}")
        time.sleep(ES_CHECK_INTERVAL_SECONDS)

    print_error(f"Elasticsearch API did not become available after {MAX_ES_WAIT_SECONDS} seconds.")
    return False

def wait_for_kibana(kibana_base_url, kibana_auth):
    """Waits for the Kibana API status endpoint to return 200."""
    start_time = time.time()
    url = f"{kibana_base_url}/api/status"
    # Note: We check status using the API user (e.g., elastic), not the internal user
    print_info(f"Waiting for Kibana API at {url} (using API user)...")
    while time.time() - start_time < MAX_KIBANA_WAIT_SECONDS:
        try:
            response = requests.get(url, auth=kibana_auth, verify=False, timeout=5)
            if response.status_code == 200:
                print_info(f"Kibana API is up! (Status {response.status_code})")
                return True
            else:
                # 503 is common during startup
                print_info(f"Kibana API not ready yet (Status: {response.status_code}). Retrying...")
        except requests.exceptions.ConnectionError:
            print_info("Kibana API connection refused. Retrying...")
        except requests.exceptions.Timeout:
            print_info("Kibana API connection timed out. Retrying...")
        except Exception as e:
            print_warning(f"Error checking Kibana status: {e}")
        time.sleep(KIBANA_CHECK_INTERVAL_SECONDS)

    print_error(f"Kibana API did not become available after {MAX_KIBANA_WAIT_SECONDS} seconds.")
    return False

def setup_kibana_user(es_base_url, es_auth):
    """Creates the dedicated user and role in Elasticsearch for Kibana's internal use."""
    print_info("Setting up dedicated Kibana user and role in Elasticsearch...")
    role_name = CUSTOM_KIBANA_ROLE_NAME
    user_name = KIBANA_SYSTEM_USER
    password = KIBANA_SYSTEM_PASSWORD

    role_url = f"{es_base_url}/_security/role/{role_name}"
    user_url = f"{es_base_url}/_security/user/{user_name}"

    # Define Kibana User, assigning custom role and kibana_admin
    user_payload = {
        "password" : password,
        "roles" : [ role_name, "kibana_admin" ], # Assign custom role AND kibana_admin
        "full_name" : "Internal Kibana System User (Custom+Admin) for MCP Test Env",
        "email" : "kibana@example.com",
        "enabled" : True
    }

    headers = {"Content-Type": "application/json"}
    success = True
    role_created_or_updated = False

    # 1. Create/Update Role using the constant payload
    try:
        print_info(f"Creating/updating role: {role_name}")
        response = requests.put(role_url, auth=es_auth, headers=headers, json=CUSTOM_KIBANA_ROLE_PAYLOAD, verify=False, timeout=10)
        if 200 <= response.status_code < 300:
             print_info(f"Role '{role_name}' created/updated successfully.")
             role_created_or_updated = True
        else:
            print_warning(f"Failed to create/update role '{role_name}' (HTTP {response.status_code}): {response.text}")
            success = False
    except requests.exceptions.RequestException as e:
        print_error(f"Error creating/updating role '{role_name}': {e}")
        success = False

    # 2. Create/Update User only if Role succeeded
    if role_created_or_updated:
        try:
            print_info(f"Creating/updating user: {user_name} with roles: {user_payload['roles']}")
            response = requests.put(user_url, auth=es_auth, headers=headers, json=user_payload, verify=False, timeout=10)
            if not (200 <= response.status_code < 300):
                print_warning(f"Failed to create/update user '{user_name}' (HTTP {response.status_code}): {response.text}")
                success = False
            else:
                 print_info(f"User '{user_name}' created/updated successfully.")
        except requests.exceptions.RequestException as e:
            print_error(f"Error creating/updating user '{user_name}': {e}")
            success = False
    else:
        print_info(f"Skipping user creation for '{user_name}' because role setup failed.")
        success = False # Mark overall setup as failed if role failed

    return success 