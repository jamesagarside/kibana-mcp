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

def setup_kibana_user(es_base_url, es_auth):
    """Creates a dedicated user and role in Elasticsearch for Kibana."""
    print_info("Setting up dedicated Kibana user and role in Elasticsearch...")
    role_name = "kibana_system_role"
    user_name = KIBANA_SYSTEM_USER
    password = KIBANA_SYSTEM_PASSWORD

    role_url = f"{es_base_url}/_security/role/{role_name}"
    user_url = f"{es_base_url}/_security/user/{user_name}"

    # Define Custom Kibana Role based on built-in 'kibana_system' role,
    # but ensure allow_restricted_indices is true for alert indices.
    # This definition is derived from inspecting the built-in role in 8.14.1
    role_payload = {
        "cluster": [
            "monitor", "manage_index_templates", "cluster:admin/xpack/monitoring/bulk",
            "manage_saml", "manage_token", "manage_oidc", "manage_enrich",
            "manage_pipeline", "manage_ilm", "manage_transform",
            "cluster:admin/xpack/security/api_key/invalidate", "grant_api_key",
            "manage_own_api_key", "cluster:admin/xpack/security/privilege/builtin/get",
            "delegate_pki", "cluster:admin/xpack/security/profile/get",
            "cluster:admin/xpack/security/profile/activate",
            "cluster:admin/xpack/security/profile/suggest",
            "cluster:admin/xpack/security/profile/has_privileges",
            "write_fleet_secrets", "manage_ml", "cluster:admin/analyze",
            "monitor_text_structure", "cancel_task"
        ],
        "global": {
            "application": {"manage": {"applications": ["kibana-*"]}},
            "profile": {"write": {"applications": ["kibana*"]}}
        },
        "indices": [
            # Kibana's own indices
            {"names": [".kibana*", ".reporting-*"], "privileges": ["all"], "allow_restricted_indices": True},
            # Monitoring (read only)
            {"names": [".monitoring-*"], "privileges": ["read", "read_cross_cluster"], "allow_restricted_indices": False},
            # Management Beats
            {"names": [".management-beats"], "privileges": ["create_index", "read", "write"], "allow_restricted_indices": False},
            # ML Indices (read)
            {"names": [".ml-anomalies*", ".ml-stats-*"], "privileges": ["read"], "allow_restricted_indices": False},
            # ML Annotations/Notifications (rw)
            {"names": [".ml-annotations*", ".ml-notifications*"], "privileges": ["read", "write"], "allow_restricted_indices": False},
            # APM config/links/sourcemaps (all, restricted)
            {"names": [".apm-agent-configuration", ".apm-custom-link", ".apm-source-map"], "privileges": ["all"], "allow_restricted_indices": True},
            # APM data (read)
            {"names": ["apm-*", "logs-apm.*", "metrics-apm.*", "traces-apm.*", "traces-apm-*"], "privileges": ["read", "read_cross_cluster"], "allow_restricted_indices": False},
            # General read/monitor
            {"names": ["*"], "privileges": ["view_index_metadata", "monitor"], "allow_restricted_indices": False},
            # Endpoint logs (read)
            {"names": [".logs-endpoint.diagnostic.collection-*"], "privileges": ["read"], "allow_restricted_indices": False},
            # Fleet (mostly all, restricted)
            {"names": [".fleet-secrets*"], "privileges": ["write", "delete", "create_index"], "allow_restricted_indices": True},
            {"names": [".fleet-actions*", ".fleet-agents*", ".fleet-artifacts*", ".fleet-enrollment-api-keys*", ".fleet-policies*", ".fleet-policies-leader*", ".fleet-servers*", ".fleet-fileds*", ".fleet-file-data-*", ".fleet-files-*", ".fleet-filedelivery-data-*", ".fleet-filedelivery-meta-*"], "privileges": ["all"], "allow_restricted_indices": True},
            {"names": ["logs-elastic_agent*"], "privileges": ["read"], "allow_restricted_indices": False},
            {"names": ["metrics-fleet_server*"], "privileges": ["all"], "allow_restricted_indices": False},
            {"names": ["logs-fleet_server*"], "privileges": ["read", "delete_index"], "allow_restricted_indices": False},
            # Security Solution (SIEM signals)
            {"names": [".siem-signals*"], "privileges": ["all"], "allow_restricted_indices": False},
            # Lists
            {"names": [".lists-*", ".items-*"], "privileges": ["all"], "allow_restricted_indices": False},
            # *** Alerting Indices (Allow restricted) ***
            {"names": [".internal.alerts*", ".alerts*", ".preview.alerts*", ".internal.preview.alerts*"], "privileges": ["all"], "allow_restricted_indices": True},
            # Endpoint Metrics/Events (read)
            {"names": ["metrics-endpoint.policy-*", "metrics-endpoint.metrics-*", "logs-endpoint.events.*"], "privileges": ["read"], "allow_restricted_indices": False},
            # Data stream lifecycle management for various logs/metrics/traces
            {"names": ["logs-*", "synthetics-*", "traces-*", "/metrics-.*&~(metrics-endpoint\\.metadata_current_default.*)/", ".logs-endpoint.action.responses-*", ".logs-endpoint.diagnostic.collection-*", ".logs-endpoint.actions-*", ".logs-endpoint.heartbeat-*", ".logs-osquery_manager.actions-*", ".logs-osquery_manager.action.responses-*", "profiling-*"], "privileges": ["indices:admin/settings/update", "indices:admin/mapping/put", "indices:admin/rollover", "indices:admin/data_stream/lifecycle/put"], "allow_restricted_indices": False},
            # Endpoint/Osquery action responses (rw)
            {"names": [".logs-endpoint.action.responses-*", ".logs-endpoint.actions-*"], "privileges": ["auto_configure", "read", "write"], "allow_restricted_indices": False},
            {"names": [".logs-osquery_manager.action.responses-*", ".logs-osquery_manager.actions-*"], "privileges": ["auto_configure", "create_index", "read", "index", "delete", "write"], "allow_restricted_indices": False},
            # Other integrations (read)
            {"names": ["logs-sentinel_one.*", "logs-crowdstrike.*"], "privileges": ["read"], "allow_restricted_indices": False},
            # Data stream deletion privileges
            {"names": [".logs-endpoint.diagnostic.collection-*", "logs-apm-*", "logs-apm.*-*", "metrics-apm-*", "metrics-apm.*-*", "traces-apm-*", "traces-apm.*-*", "synthetics-http-*", "synthetics-icmp-*", "synthetics-tcp-*", "synthetics-browser-*", "synthetics-browser.network-*", "synthetics-browser.screenshot-*"], "privileges": ["indices:admin/delete"], "allow_restricted_indices": False},
            # Endpoint metadata
            {"names": ["metrics-endpoint.metadata*"], "privileges": ["read", "view_index_metadata"], "allow_restricted_indices": False},
            {"names": [".metrics-endpoint.metadata_current_default*", ".metrics-endpoint.metadata_united_default*"], "privileges": ["create_index", "delete_index", "read", "index", "indices:admin/aliases", "indices:admin/settings/update"], "allow_restricted_indices": False},
             # Threat Intel indices
            {"names": ["logs-ti_*_latest.*"], "privileges": ["create_index", "delete_index", "read", "index", "delete", "manage", "indices:admin/aliases", "indices:admin/settings/update"], "allow_restricted_indices": False},
            {"names": ["logs-ti_*.*-*"], "privileges": ["indices:admin/delete", "read", "view_index_metadata"], "allow_restricted_indices": False},
            # Sample data
            {"names": ["kibana_sample_data_*"], "privileges": ["create_index", "delete_index", "read", "index", "view_index_metadata", "indices:admin/aliases", "indices:admin/settings/update"], "allow_restricted_indices": False},
            # CSP data
            {"names": ["logs-cloud_security_posture.findings-*", "logs-cloud_security_posture.vulnerabilities-*"], "privileges": ["read", "view_index_metadata"], "allow_restricted_indices": False},
            {"names": ["logs-cloud_security_posture.findings_latest-default*", "logs-cloud_security_posture.scores-default*", "logs-cloud_security_posture.vulnerabilities_latest-default*"], "privileges": ["create_index", "read", "index", "delete", "indices:admin/aliases", "indices:admin/settings/update"], "allow_restricted_indices": False},
            # Risk score
            {"names": ["risk-score.risk-*"], "privileges": ["all"], "allow_restricted_indices": False},
            # Asset criticality
            {"names": [".asset-criticality.asset-criticality-*"], "privileges": ["create_index", "manage", "read"], "allow_restricted_indices": False},
            # Cloud Defend
            {"names": ["logs-cloud_defend.*", "metrics-cloud_defend.*"], "privileges": ["read", "view_index_metadata"], "allow_restricted_indices": False},
            # SLO
            {"names": [".slo-observability.*"], "privileges": ["all"], "allow_restricted_indices": False},
            # Endpoint heartbeat (read)
            {"names": [".logs-endpoint.heartbeat-*"], "privileges": ["read"], "allow_restricted_indices": False},
            # Connectors
            {"names": [".elastic-connectors*"], "privileges": ["read"], "allow_restricted_indices": False}
        ],
        "applications": [],
        "run_as": [],
        "metadata": {},
        "transient_metadata": {"enabled": True}
        # No remote_indices section needed for this custom role
    }

    # Define Kibana User, assigning ONLY the custom role
    user_payload = {
        "password" : password,
        "roles" : [ role_name ], # Assign ONLY the custom role
        "full_name" : "Internal Kibana System User (Custom Role) for MCP Test Env",
        "email" : "kibana@example.com",
        "enabled" : True
    }

    headers = {"Content-Type": "application/json"}
    success = True
    role_created_or_updated = False

    # 1. Create/Update Role
    try:
        print_info(f"Creating/updating role: {role_name}")
        # Use PUT to ensure the role exists with the desired definition
        response = requests.put(role_url, auth=es_auth, headers=headers, json=role_payload, verify=False, timeout=10)
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
            print_info(f"Creating/updating user: {user_name} with role '{role_name}'")
            # Use PUT to ensure user exists and has the correct role assignment
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
    # Use the custom user name for kibana_auth
    kibana_auth = (KIBANA_SYSTEM_USER, KIBANA_SYSTEM_PASSWORD)

    # 3. Start Docker Services
    print_info("Starting Docker Compose services...")
    if not run_compose_command(compose_cmd, "up", "-d"):
        print_error("Failed to start Docker Compose services. Check logs above.")
        run_compose_command(compose_cmd, "logs")
        sys.exit(1)

    alerts_verified = False
    trigger_doc_written = False
    kibana_user_setup = False # Reset flag
    es_ready = False

    # 4. Wait for Elasticsearch
    es_ready = wait_for_elasticsearch(es_base_url, es_auth)

    if not es_ready:
        print_error("Elasticsearch did not become ready. Aborting setup.")
        run_compose_command(compose_cmd, "logs", "elasticsearch") # Show ES logs on failure
        sys.exit(1)

    # 5. Setup Kibana User and Role
    print_info("Attempting to setup Kibana user and role in Elasticsearch...")
    kibana_user_setup = setup_kibana_user(es_base_url, es_auth)

    if not kibana_user_setup:
        print_error("Failed to setup Kibana user and/or role in Elasticsearch.")
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
    print(f" -> Kibana:        {kibana_base_url} (User: {KIBANA_SYSTEM_USER}, Pass: {KIBANA_SYSTEM_PASSWORD})")
    print("\nNote:") # Simplified
    es_status = 'Success' if es_ready else 'Failed'
    pw_status = 'Success' if kibana_user_setup else 'Failed'
    trig_status = 'Success' if trigger_doc_written else 'Failed'
    print(f"      Elasticsearch ready status: {es_status}")
    print(f"      Kibana user setup status: {'Success' if kibana_user_setup else 'Failed'}")
    print(f"      Trigger document write status: {trig_status}")
    if alerts_verified:
        print("      Successfully verified that alerts were generated.")
    else:
        print("      WARNING: Could not verify alerts within time limit.") # Simplified
    print(f"\nTo stop services: {compose_down_cmd}")
    print("-" * 53)

if __name__ == "__main__":
    main() 