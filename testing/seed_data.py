import os
import subprocess
import sys
import time
import json
import requests
import yaml  # Requires PyYAML
from pathlib import Path

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
COMPOSE_FILE = SCRIPT_DIR / "docker-compose.yml"
SAMPLE_RULE_FILE = SCRIPT_DIR / "sample_rule.json"
DEFAULT_USER = "elastic"
MAX_KIBANA_WAIT_SECONDS = 180  # 3 minutes
KIBANA_CHECK_INTERVAL_SECONDS = 5

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
        print_info(f"Command successful:
{result.stdout}")
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

def wait_for_kibana(kibana_base_url, auth):
    """Waits for the Kibana API status endpoint to return 200."""
    start_time = time.time()
    url = f"{kibana_base_url}/api/status"
    print_info(f"Waiting for Kibana API at {url}...")
    while time.time() - start_time < MAX_KIBANA_WAIT_SECONDS:
        try:
            response = requests.get(url, auth=auth, verify=False, timeout=5) # Added verify=False for local testing
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

def create_sample_alert_rule(kibana_base_url, auth):
    """Creates a sample alert rule using the Kibana API."""
    url = f"{kibana_base_url}/api/alerting/rule"
    print_info("Attempting to create sample alert rule via Kibana API...")
    try:
        with open(SAMPLE_RULE_FILE, 'r') as f:
            rule_payload = json.load(f)

        headers = {
            "kbn-xsrf": "true",
            "Content-Type": "application/json"
        }
        response = requests.post(
            url,
            auth=auth,
            headers=headers,
            json=rule_payload,
            verify=False, # Added verify=False for local testing
            timeout=15
        )

        if 200 <= response.status_code < 300:
            print_info(f"Successfully created/updated sample alert rule (HTTP {response.status_code}). Alerts should generate soon.")
        elif response.status_code == 409:
            print_info(f"Sample alert rule likely already exists (HTTP {response.status_code}).")
        else:
            print_warning(f"Failed to create sample alert rule (HTTP {response.status_code}). Response: {response.text}")

    except FileNotFoundError:
        print_error(f"Sample rule file not found at {SAMPLE_RULE_FILE}")
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse sample rule file {SAMPLE_RULE_FILE}: {e}")
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to send request to create rule: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred creating the rule: {e}")

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
    auth = (DEFAULT_USER, es_password)

    # 3. Start Docker Services
    print_info("Starting Docker Compose services in detached mode...")
    if not run_compose_command(compose_cmd, "up", "-d"):
        print_error("Failed to start Docker Compose services. Check logs above.")
        # Attempt to show logs
        run_compose_command(compose_cmd, "logs")
        sys.exit(1)

    # 4. Wait for Kibana & Seed Data
    if wait_for_kibana(kibana_base_url, auth):
        create_sample_alert_rule(kibana_base_url, auth)
    else:
        print_warning("Could not confirm Kibana status, skipping sample alert creation.")

    # 5. Output Information
    print("\n" + "-" * 53)
    print(" Elasticsearch & Kibana Quickstart Setup Complete!")
    print("-" * 53 + "\n")
    print("Services are running in the background.")
    print(f"Check status:   {' '.join(compose_cmd)} -f \"{COMPOSE_FILE}\" ps")
    print(f"View logs:      {' '.join(compose_cmd)} -f \"{COMPOSE_FILE}\" logs -f")
    print("\nAccess Details:")
    print(f" -> Elasticsearch: {es_base_url}")
    print(f" -> Kibana:        {kibana_base_url}")
    print("\nCredentials:")
    print(f" -> Username: {DEFAULT_USER}")
    print(f" -> Password: {es_password} (from {COMPOSE_FILE.name})")
    print("\nNote: Sample alert rule creation attempted. Check logs above for status.")
    print("      Alerts should appear in Kibana shortly if successful.")
    print(f"\nTo stop services: {' '.join(compose_cmd)} -f \"{COMPOSE_FILE}\" down")
    print("-" * 53)

if __name__ == "__main__":
    main() 