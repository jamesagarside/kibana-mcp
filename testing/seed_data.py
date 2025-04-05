import os
import subprocess
import sys
import time
import json
import requests
import yaml  # Requires PyYAML
from pathlib import Path
import datetime

# Use relative imports now that testing is a package
from .config import (
    COMPOSE_FILE, DEFAULT_USER, KIBANA_SYSTEM_USER # Add other needed constants
)
from .utils import print_info, print_error, command_exists
from .docker_utils import (
    get_docker_compose_cmd, run_compose_command, parse_compose_config
)
from .es_kb_setup import (
    wait_for_elasticsearch, wait_for_kibana, setup_kibana_user
)
from .detection import (
    create_sample_detection_rule, write_trigger_document, wait_for_signals
)

# ==============================================================================
# --- Configuration Constants ---
# ==============================================================================
# SCRIPT_DIR = Path(__file__).parent.resolve()
# COMPOSE_FILE = SCRIPT_DIR / "docker-compose.yml"
# SAMPLE_RULE_FILE = SCRIPT_DIR / "sample_rule.json"
# TRIGGER_DOC_FILE = SCRIPT_DIR / "trigger_document.json"
# DEFAULT_USER = "elastic"
# MAX_KIBANA_WAIT_SECONDS = 180  # 3 minutes
# KIBANA_CHECK_INTERVAL_SECONDS = 5
# MAX_ALERT_WAIT_SECONDS = 150  # Wait up to 2.5 minutes for signals (increased from 90)
# ALERT_CHECK_INTERVAL_SECONDS = 10
# KIBANA_SYSTEM_USER = "kibana_system_user"
# KIBANA_SYSTEM_PASSWORD = "kibanapass" # Hardcoded for simplicity in testing setup
# MAX_ES_WAIT_SECONDS = 90  # Wait up to 1.5 minutes for ES
# ES_CHECK_INTERVAL_SECONDS = 5

# --- Custom Kibana Role Definition ---
# CUSTOM_KIBANA_ROLE_NAME = "kibana_system_role"
# CUSTOM_KIBANA_ROLE_PAYLOAD = { ... } # Defined in config.py


# ==============================================================================
# --- Utilities ---
# ==============================================================================
# def print_info(msg):
#     print(f"[INFO] {msg}")
#
# def print_warning(msg):
#     print(f"[WARNING] {msg}", file=sys.stderr)
#
# def print_error(msg):
#     print(f"[ERROR] {msg}", file=sys.stderr)
#
# def command_exists(cmd):
#     try:
#         subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
#         return True
#     except (subprocess.CalledProcessError, FileNotFoundError):
#         return False


# ==============================================================================
# --- Docker Management ---
# ==============================================================================
# def get_docker_compose_cmd():
#     """Determines whether to use 'docker compose' or 'docker-compose'"""
#     try:
#         # Check V2 first
#         subprocess.run(["docker", "compose", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
#         print_info("Using Docker Compose V2 ('docker compose')")
#         return ["docker", "compose"]
#     except (subprocess.CalledProcessError, FileNotFoundError):
#         if command_exists("docker-compose"):
#             print_info("Using Docker Compose V1 ('docker-compose')")
#             return ["docker-compose"]
#         else:
#             return None
#
# def run_compose_command(compose_cmd_base, *args):
#     cmd = compose_cmd_base + ["-f", str(COMPOSE_FILE)] + list(args)
#     print_info(f"Running: {' '.join(cmd)}")
#     try:
#         # Use run instead of Popen for simpler commands, capture output if needed
#         result = subprocess.run(cmd, check=True, capture_output=True, text=True)
#         print_info(f"Command successful:")
#         if result.stdout:
#             print(result.stdout) # Print stdout on a new line if it exists
#         return True
#     except subprocess.CalledProcessError as e:
#         print_error(f"Docker Compose command failed: {' '.join(cmd)}")
#         print_error(f"Stderr:\n{e.stderr}")
#         print_error(f"Stdout:\n{e.stdout}")
#         return False
#     except Exception as e:
#         print_error(f"An unexpected error occurred running compose: {e}")
#         return False
#
# def parse_compose_config():
#     """Parses docker-compose.yml to extract ports and password."""
#     config = {"es_port": "9200", "kibana_port": "5601", "es_password": "elastic"}
#     try:
#         with open(COMPOSE_FILE, 'r') as f:
#             compose_data = yaml.safe_load(f)
#
#         # Extract Elasticsearch port
#         es_ports = compose_data.get('services', {}).get('elasticsearch', {}).get('ports', [])
#         for port_mapping in es_ports:
#             if str(port_mapping).endswith(":9200"):
#                 config["es_port"] = str(port_mapping).split(":")[0].strip('"')
#                 break
#
#         # Extract Kibana port
#         kibana_ports = compose_data.get('services', {}).get('kibana', {}).get('ports', [])
#         for port_mapping in kibana_ports:
#             if str(port_mapping).endswith(":5601"):
#                 config["kibana_port"] = str(port_mapping).split(":")[0].strip('"')
#                 break
#
#         # Extract Elasticsearch password
#         es_env = compose_data.get('services', {}).get('elasticsearch', {}).get('environment', {})
#         # Handle both list and dict formats for environment variables
#         if isinstance(es_env, list):
#             for env_var in es_env:
#                 if env_var.startswith("ELASTIC_PASSWORD="):
#                     config["es_password"] = env_var.split("=", 1)[1].strip('"')
#                     break
#         elif isinstance(es_env, dict):
#              config["es_password"] = es_env.get("ELASTIC_PASSWORD", config["es_password"])
#
#     except FileNotFoundError:
#         print_error(f"Compose file not found at {COMPOSE_FILE}")
#         sys.exit(1)
#     except Exception as e:
#         print_warning(f"Could not parse {COMPOSE_FILE}: {e}. Using defaults.")
#
#     print_info(f"Parsed config: Ports(ES:{config['es_port']}, Kibana:{config['kibana_port']}), Password:{config['es_password']}")
#     return config


# ==============================================================================
# --- Detection Rule / Signal Management ---
# ==============================================================================
# def create_sample_detection_rule(kibana_base_url, kibana_auth):
#     # ... moved ...
#
# def write_trigger_document(es_base_url, es_auth):
#     # ... moved ...
#
# def wait_for_signals(kibana_base_url, kibana_auth, rule_id):
#     # ... moved ...


# ==============================================================================
# --- Main Execution Logic ---
# ==============================================================================
def main():
    print_info("Starting Kibana/Elasticsearch Test Environment Setup...")

    # --- 1. Prerequisites and Configuration ---
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

    # Pass COMPOSE_FILE to parse_compose_config
    config = parse_compose_config(COMPOSE_FILE)
    kibana_port = config["kibana_port"]
    es_port = config["es_port"]
    es_password = config["es_password"]
    kibana_base_url = f"http://localhost:{kibana_port}"
    es_base_url = f"http://localhost:{es_port}"
    es_auth = (DEFAULT_USER, es_password)
    kibana_api_auth = es_auth # Use elastic user for script API calls

    # --- Initialize Status Flags ---
    signals_verified = False
    trigger_doc_written = False
    kibana_user_setup = False
    es_ready = False

    # --- 2. Start Docker Services ---
    print_info("Starting Docker Compose services...")
    # Pass COMPOSE_FILE and compose_cmd
    if not run_compose_command(COMPOSE_FILE, compose_cmd, "up", "-d"):
        print_error("Failed to start Docker Compose services. Check logs above.")
        run_compose_command(COMPOSE_FILE, compose_cmd, "logs")
        sys.exit(1)

    # --- 3. Wait for Elasticsearch ---
    es_ready = wait_for_elasticsearch(es_base_url, es_auth)
    if not es_ready:
        print_error("Elasticsearch did not become ready. Aborting setup.")
        run_compose_command(COMPOSE_FILE, compose_cmd, "logs", "elasticsearch")
        sys.exit(1)

    # --- 4. Setup Kibana Internal User ---
    print_info("Attempting to setup Kibana user and role for Kibana internal use...")
    kibana_user_setup = setup_kibana_user(es_base_url, es_auth)
    if not kibana_user_setup:
        print_error("Failed to setup Kibana user/role for Kibana internal use.")
        sys.exit(1)

    # --- 5. Wait for Kibana and Run Test Logic ---
    print_info("Waiting for Kibana API to become available...")
    if wait_for_kibana(kibana_base_url, kibana_api_auth):
        print_info("Kibana API ready. Proceeding with rule creation and test...")
        # Create the rule FIRST
        rule_id = create_sample_detection_rule(kibana_base_url, kibana_api_auth)
        if rule_id:
            # Write the trigger document SECOND
            trigger_doc_written = write_trigger_document(es_base_url, es_auth)
            if not trigger_doc_written:
                 print_warning("Failed to write trigger document, signal generation might not occur.")
            # Wait for signals THIRD
            signals_verified = wait_for_signals(kibana_base_url, kibana_api_auth, rule_id)
        else:
            print_warning("Skipping trigger document write and signal verification as rule creation failed or rule ID unavailable.")
    else:
        print_warning("Kibana API did not become available, skipping rule creation and test.")

    # --- 6. Output Summary ---
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
    print(f" -> Kibana:        {kibana_base_url} (Internal User: {KIBANA_SYSTEM_USER}, API Calls Use: {DEFAULT_USER})")
    print("\nSetup Status:")
    print(f"  - Elasticsearch Ready: {'Success' if es_ready else 'Failed'}")
    print(f"  - Kibana Internal User Setup: {'Success' if kibana_user_setup else 'Failed'}")
    print(f"  - Trigger Document Write: {'Success' if trigger_doc_written else 'Failed'}")
    if signals_verified:
        print("  - Detection Signals Verified: Success")
    else:
        print("  - Detection Signals Verified: Failed (WARNING: Could not verify within time limit)")
    print(f"\nTo stop services: {compose_down_cmd}")
    print("-" * 53)

if __name__ == "__main__":
    main() 