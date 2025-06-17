import sys  # Keep sys for sys.exit

# Use relative imports now that testing is a package
from .config import (
    DEFAULT_USER
)
from .utils import print_info, print_error, print_warning

from .es_kb_setup import (
    create_index_template  # Import the new function
)
from .detection import (
    create_sample_detection_rule, write_auth_data, wait_for_signals
)

# ==============================================================================
# --- Main Execution Logic ---
# ==============================================================================


def main():
    print_info("Starting Kibana/Elasticsearch Test Environment Setup...")
    # --- 1. Prerequisites and Configuration ---

    # Pass COMPOSE_FILE to parse_compose_config
    kibana_port = 5601
    es_port = 9200
    es_password = "changeme"
    kibana_base_url = f"https://localhost:{kibana_port}"
    es_base_url = f"https://localhost:{es_port}"
    es_auth = (DEFAULT_USER, es_password)
    kibana_api_auth = es_auth  # Use elastic user for script API calls

    # --- Initialize Status Flags ---
    signals_verified = False
    trigger_doc_written = False
    kibana_user_setup = False
    es_ready = False

    # --- 4. Setup Kibana Internal User and Index Template ---
    print_info("Attempting to create index template for auth logs...")
    if not create_index_template(es_base_url, es_auth):
        print_error(
            "Failed to create index template. Proceeding, but rule might fail.")
        # Decide if this should be fatal - for now, just warn
        # sys.exit(1)

    # --- 5. Wait for Kibana and Run Test Logic ---
    print_info("Configuring Detection Rule and Writing Auth Data...")
    # Create the rule FIRST
    rule_id = create_sample_detection_rule(
        kibana_base_url, kibana_api_auth)
    if rule_id:
        # Write the auth data SECOND
        trigger_doc_written = write_auth_data(es_base_url, es_auth)
        if not trigger_doc_written:
            print_warning(
                "Failed to write auth data, signal generation might not occur.")
        # Wait for signals THIRD
        signals_verified = wait_for_signals(
            kibana_base_url, kibana_api_auth, rule_id)
    else:
        print_warning(
            "Skipping auth data write and signal verification as rule creation failed or rule ID unavailable.")


if __name__ == "__main__":
    main()
