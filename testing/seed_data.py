import sys # Keep sys for sys.exit

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