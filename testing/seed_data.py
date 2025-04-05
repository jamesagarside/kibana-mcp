import os
import subprocess
import sys
import time
import json
import requests
import yaml  # Requires PyYAML
from pathlib import Path
import datetime

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
COMPOSE_FILE = SCRIPT_DIR / "docker-compose.yml"
SAMPLE_RULE_FILE = SCRIPT_DIR / "sample_rule.json"
TRIGGER_DOC_FILE = SCRIPT_DIR / "trigger_document.json"
DEFAULT_USER = "elastic"
MAX_KIBANA_WAIT_SECONDS = 180  # 3 minutes
KIBANA_CHECK_INTERVAL_SECONDS = 5
MAX_ALERT_WAIT_SECONDS = 90  # Wait up to 1.5 minutes for alerts
ALERT_CHECK_INTERVAL_SECONDS = 10
KIBANA_SYSTEM_USER = "kibana_system_user"
KIBANA_SYSTEM_PASSWORD = "kibanapass" # Hardcoded for simplicity in testing setup
MAX_ES_WAIT_SECONDS = 90  # Wait up to 1.5 minutes for ES
ES_CHECK_INTERVAL_SECONDS = 5

# --- Helper Functions ---
def print_info(msg):
    print(f"[INFO] {msg}")

def print_warning(msg):
    print(f"[WARNING] {msg}", file=sys.stderr)

def print_error(msg):
    print(f"[ERROR] {msg}", file=sys.stderr)

def command_exists(cmd):
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_docker_compose_cmd():
    """Determines whether to use 'docker compose' or 'docker-compose'"""
    try:
        # Check V2 first
        subprocess.run(["docker", "compose", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print_info("Using Docker Compose V2 ('docker compose')")
        return ["docker", "compose"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        if command_exists("docker-compose"):
            print_info("Using Docker Compose V1 ('docker-compose')")
            return ["docker-compose"]
        else:
            return None

def run_compose_command(compose_cmd_base, *args):
    cmd = compose_cmd_base + ["-f", str(COMPOSE_FILE)] + list(args)
    print_info(f"Running: {' '.join(cmd)}")
    try:
        # Use run instead of Popen for simpler commands, capture output if needed
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_info(f"Command successful:")
        if result.stdout:
            print(result.stdout) # Print stdout on a new line if it exists
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Docker Compose command failed: {' '.join(cmd)}")
        print_error(f"Stderr:\n{e.stderr}")
        print_error(f"Stdout:\n{e.stdout}")
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred running compose: {e}")
        return False

def parse_compose_config():
    """Parses docker-compose.yml to extract ports and password."""
    config = {"es_port": "9200", "kibana_port": "5601", "es_password": "elastic"}
    try:
        with open(COMPOSE_FILE, 'r') as f:
            compose_data = yaml.safe_load(f)

        # Extract Elasticsearch port
        es_ports = compose_data.get('services', {}).get('elasticsearch', {}).get('ports', [])
        for port_mapping in es_ports:
            if str(port_mapping).endswith(":9200"):
                config["es_port"] = str(port_mapping).split(":")[0].strip('"')
                break

        # Extract Kibana port
        kibana_ports = compose_data.get('services', {}).get('kibana', {}).get('ports', [])
        for port_mapping in kibana_ports:
            if str(port_mapping).endswith(":5601"):
                config["kibana_port"] = str(port_mapping).split(":")[0].strip('"')
                break

        # Extract Elasticsearch password
        es_env = compose_data.get('services', {}).get('elasticsearch', {}).get('environment', {})
        # Handle both list and dict formats for environment variables
        if isinstance(es_env, list):
            for env_var in es_env:
                if env_var.startswith("ELASTIC_PASSWORD="):
                    config["es_password"] = env_var.split("=", 1)[1].strip('"')
                    break
        elif isinstance(es_env, dict):
             config["es_password"] = es_env.get("ELASTIC_PASSWORD", config["es_password"])

    except FileNotFoundError:
        print_error(f"Compose file not found at {COMPOSE_FILE}")
        sys.exit(1)
    except Exception as e:
        print_warning(f"Could not parse {COMPOSE_FILE}: {e}. Using defaults.")

    print_info(f"Parsed config: Ports(ES:{config['es_port']}, Kibana:{config['kibana_port']}), Password:{config['es_password']}")
    return config

def wait_for_kibana(kibana_base_url, kibana_auth):
    """Waits for the Kibana API status endpoint to return 200."""
    start_time = time.time()
    url = f"{kibana_base_url}/api/status"
    print_info(f"Waiting for Kibana API at {url} (using '{KIBANA_SYSTEM_USER}')...")
    while time.time() - start_time < MAX_KIBANA_WAIT_SECONDS:
        try:
            response = requests.get(url, auth=kibana_auth, verify=False, timeout=5)
            if response.status_code == 200:
                print_info(f"Kibana API is up! (Status {response.status_code})")
                return True
            else:
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

def create_sample_alert_rule(kibana_base_url, kibana_auth):
    """Creates a sample alert rule using the Kibana API. Returns the rule name on success, None otherwise."""
    url = f"{kibana_base_url}/api/alerting/rule"
    rule_name = None
    print_info("Attempting to create sample alert rule via Kibana API...")
    try:
        with open(SAMPLE_RULE_FILE, 'r') as f:
            rule_payload = json.load(f)
            rule_name = rule_payload.get("name") # Extract rule name

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
            verify=False, # Added verify=False for local testing
            timeout=15
        )

        if 200 <= response.status_code < 300:
            print_info(f"Successfully created/updated sample alert rule '{rule_name}' (HTTP {response.status_code}).")
            return rule_name
        elif response.status_code == 409:
            print_info(f"Sample alert rule '{rule_name}' likely already exists (HTTP {response.status_code}).")
            return rule_name # Assume it exists and proceed
        else:
            print_warning(f"Failed to create sample alert rule (HTTP {response.status_code}). Response: {response.text}")
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

def wait_for_alerts(kibana_base_url, kibana_auth, rule_name):
    """Waits for alerts generated by the specified rule name to appear."""
    if not rule_name:
        print_warning("Cannot wait for alerts without a valid rule name.")
        return False

    start_time = time.time()
    url = f"{kibana_base_url}/api/alerting/alerts/_find"
    print_info(f"Waiting up to {MAX_ALERT_WAIT_SECONDS}s for alerts from rule '{rule_name}' to be generated...")

    find_payload = {
        "page": 1,
        "per_page": 1,
        "sort_field": "start",
        "sort_order": "desc",
        # Use filter instead of search for exact match on generated_by rule name
        # Filter syntax might depend on exact Kibana version
        # Build filter string using concatenation
        "filter": 'alert.attributes.ruleName: "' + rule_name + '" or kibana.alert.rule.name: "' + rule_name + '"'
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
                json=find_payload,
                verify=False,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                alert_count = data.get('total', 0)
                if alert_count > 0:
                    print_info(f"Successfully found {alert_count} alert(s) generated by rule '{rule_name}'.")
                    return True
                else:
                    print_info(f"Found 0 alerts from rule '{rule_name}' yet. Checking again in {ALERT_CHECK_INTERVAL_SECONDS}s...")
            else:
                print_warning(f"Alert find query failed (HTTP {response.status_code}). Retrying...")

        except requests.exceptions.RequestException as e:
            print_warning(f"Error querying alerts: {e}. Retrying...")
        except Exception as e:
            print_warning(f"Unexpected error querying alerts: {e}. Retrying...")

        time.sleep(ALERT_CHECK_INTERVAL_SECONDS)

    print_error(f"Timed out after {MAX_ALERT_WAIT_SECONDS}s waiting for alerts from rule '{rule_name}'.")
    return False

def write_trigger_document(es_base_url, es_auth):
    """Writes a document (from JSON file) to Elasticsearch to trigger the sample alert rule."""
    if not TRIGGER_DOC_FILE.exists():
        print_error(f"Trigger document file not found: {TRIGGER_DOC_FILE}")
        return False

    url = f"{es_base_url}/_bulk"
    # Use a non-restricted index name to avoid auto_create permission issues
    index_name = "mcp-trigger-docs"
    print_info(f"Writing trigger document from {TRIGGER_DOC_FILE.name} to Elasticsearch index '{index_name}'...")

    try:
        # Read the base document from the JSON file
        with open(TRIGGER_DOC_FILE, 'r') as f:
            trigger_doc_base = json.load(f)

        # Add current timestamp
        trigger_doc_base['@timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Elasticsearch Bulk API format: action_and_meta_data\n optional_source\n
        action_meta = json.dumps({"index": {"_index": index_name}})
        source_doc = json.dumps(trigger_doc_base)

        bulk_data = f"{action_meta}\n{source_doc}\n"

        headers = {
            "Content-Type": "application/x-ndjson"
        }

        response = requests.post(
            url,
            auth=es_auth,
            headers=headers,
            data=bulk_data.encode('utf-8'), # Send raw bytes
            verify=False, # For local testing
            timeout=10
        )

        if response.status_code == 200:
            response_json = response.json()
            if response_json.get("errors"):
                print_warning(f"Elasticsearch Bulk API reported errors: {response_json}")
                return False
            else:
                print_info("Successfully wrote trigger document to Elasticsearch.")
                return True
        else:
            print_warning(f"Failed to write trigger document (HTTP {response.status_code}). Response: {response.text}")
            return False

    except FileNotFoundError:
        # Should be caught by the check at the start, but belt-and-suspenders
        print_error(f"Trigger document file not found: {TRIGGER_DOC_FILE}")
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse trigger document file {TRIGGER_DOC_FILE}: {e}")
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to send request to Elasticsearch _bulk API: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred writing trigger document: {e}")

    return False

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
                # Optional: Check cluster health endpoint as well?
                # health_url = f"{es_base_url}/_cluster/health?wait_for_status=yellow&timeout=5s"
                # health_response = requests.get(health_url, auth=es_auth, verify=False, timeout=7)
                # if health_response.status_code == 200:
                #    print_info("Elasticsearch cluster health is yellow or green.")
                #    return True
                # else:
                #    print_info(f"ES cluster health status: {health_response.status_code}. Retrying...")
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

def set_builtin_user_password(es_base_url, es_auth, username, password):
    """Sets the password for a built-in Elasticsearch user."""
    # Cannot modify roles for reserved users, only password.
    print_info(f"Setting password for built-in user: {username}...")
    url = f"{es_base_url}/_security/user/{username}/_password"
    headers = {"Content-Type": "application/json"}
    payload = {"password": password}
    success = True
    try:
        # Use the admin user (es_auth) to set the password for the target user
        response = requests.post(url, auth=es_auth, headers=headers, json=payload, verify=False, timeout=10)
        if not (200 <= response.status_code < 300):
            # Handle case where password might already be set (e.g., 400 bad request if same pw)
            if response.status_code == 400 and "password is unchanged" in response.text:
                 print_info(f"Password for user '{username}' is likely already set to the desired value.")
            else:
                print_warning(f"Failed to set password for user '{username}' (HTTP {response.status_code}): {response.text}")
                success = False
        else:
            print_info(f"Password for user '{username}' set successfully.")
    except requests.exceptions.RequestException as e:
        print_error(f"Error setting password for user '{username}': {e}")
        success = False
    return success

# --- Main Execution ---
def main():
    print_info("Starting Kibana/Elasticsearch Test Environment Setup...")

    # 1. Check prerequisites
    print_info("Checking prerequisites...")
    if not command_exists("docker"):
        print_error("Docker is not installed or not in PATH. Please install Docker.")
        sys.exit(1)

    compose_cmd = get_docker_compose_cmd()
    if not compose_cmd:
        print_error("Docker Compose (v1 or v2) is not installed or available.")
        sys.exit(1)

    if not COMPOSE_FILE.exists():
        print_error(f"Compose file not found at {COMPOSE_FILE}")
        sys.exit(1)

    # 2. Parse Config
    config = parse_compose_config()
    kibana_port = config["kibana_port"]
    es_port = config["es_port"]
    es_password = config["es_password"]
    kibana_base_url = f"http://localhost:{kibana_port}"
    es_base_url = f"http://localhost:{es_port}"
    es_auth = (DEFAULT_USER, es_password)
    # Define kibana_auth using the BUILT-IN user name now
    kibana_auth = ("kibana_system", KIBANA_SYSTEM_PASSWORD)

    # 3. Start Docker Services
    print_info("Starting Docker Compose services...")
    if not run_compose_command(compose_cmd, "up", "-d"):
        print_error("Failed to start Docker Compose services. Check logs above.")
        run_compose_command(compose_cmd, "logs")
        sys.exit(1)

    alerts_verified = False
    trigger_doc_written = False
    kibana_user_setup = False # Reset flag - represents setting the password now
    es_ready = False

    # 4. Wait for Elasticsearch
    es_ready = wait_for_elasticsearch(es_base_url, es_auth)

    if not es_ready:
        print_error("Elasticsearch did not become ready. Aborting setup.")
        run_compose_command(compose_cmd, "logs", "elasticsearch") # Show ES logs on failure
        sys.exit(1)

    # 5. Set Password for Built-in Kibana User (instead of creating user/role)
    kibana_user_setup = set_builtin_user_password(es_base_url, es_auth, "kibana_system", KIBANA_SYSTEM_PASSWORD)

    if not kibana_user_setup:
        print_error("Failed to set password for built-in kibana_system user.")
        # No point continuing if Kibana can't authenticate
        sys.exit(1)

    # 6. Wait for Kibana & Seed Data (Use kibana_auth)
    if wait_for_kibana(kibana_base_url, kibana_auth):
        # Write the trigger document (using ES admin user)
        trigger_doc_written = write_trigger_document(es_base_url, es_auth)
        if not trigger_doc_written:
             print_warning("Failed to write trigger document, alert generation might not occur.")

        # Create the rule (using Kibana system user via kibana_auth)
        rule_name = create_sample_alert_rule(kibana_base_url, kibana_auth)
        if rule_name:
            # Wait for alerts (using Kibana system user via kibana_auth)
            alerts_verified = wait_for_alerts(kibana_base_url, kibana_auth, rule_name)
        else:
            print_warning("Skipping alert verification as rule creation failed or rule name unavailable.")
    else:
        print_warning("Could not confirm Kibana status, skipping sample rule creation and alert verification.")

    # 7. Output Information
    print("\n" + "-" * 53)
    print(" Elasticsearch & Kibana Quickstart Setup Complete!")
    print("-" * 53 + "\n")
    print("Services are running in the background.")
    compose_ps_cmd = ' '.join(compose_cmd) + f' -f "{COMPOSE_FILE}" ps'
    compose_logs_cmd = ' '.join(compose_cmd) + f' -f "{COMPOSE_FILE}" logs -f'
    compose_down_cmd = ' '.join(compose_cmd) + f' -f "{COMPOSE_FILE}" down'
    print(f"Check status:   {compose_ps_cmd}")
    print(f"View logs:      {compose_logs_cmd}")
    print("\nAccess Details:")
    print(f" -> Elasticsearch: {es_base_url} (User: {DEFAULT_USER}, Pass: {es_password})")
    print(f" -> Kibana:        {kibana_base_url} (Uses built-in 'kibana_system', Pass: {KIBANA_SYSTEM_PASSWORD})")
    print("\nNote:") # Simplified
    es_status = 'Success' if es_ready else 'Failed'
    pw_status = 'Success' if kibana_user_setup else 'Failed'
    trig_status = 'Success' if trigger_doc_written else 'Failed'
    print(f"      Elasticsearch ready status: {es_status}")
    print(f"      Kibana built-in user password set status: {pw_status}")
    print(f"      Trigger document write status: {trig_status}")
    if alerts_verified:
        print("      Successfully verified that alerts were generated.")
    else:
        print("      WARNING: Could not verify alerts within time limit.") # Simplified
    print(f"\nTo stop services: {compose_down_cmd}")
    print("-" * 53)

if __name__ == "__main__":
    main() 