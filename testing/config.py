from pathlib import Path

# ==============================================================================
# --- Configuration Constants ---
# ==============================================================================
# Use Path(__file__) for relative paths within module
SCRIPT_DIR = Path(__file__).parent.resolve()
SAMPLE_RULE_FILE = SCRIPT_DIR / "sample_rule.json"
NDJSON_FILE = SCRIPT_DIR / "auth_events.ndjson"
DEFAULT_USER = "elastic"
MAX_KIBANA_WAIT_SECONDS = 180  # 3 minutes
KIBANA_CHECK_INTERVAL_SECONDS = 5
MAX_ALERT_WAIT_SECONDS = 150  # Wait up to 2.5 minutes for signals
ALERT_CHECK_INTERVAL_SECONDS = 10
MAX_ES_WAIT_SECONDS = 90  # Wait up to 1.5 minutes for ES
ES_CHECK_INTERVAL_SECONDS = 5
