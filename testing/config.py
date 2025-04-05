from pathlib import Path

# ==============================================================================
# --- Configuration Constants ---
# ==============================================================================
SCRIPT_DIR = Path(__file__).parent.resolve() # Use Path(__file__) for relative paths within module
COMPOSE_FILE = SCRIPT_DIR / "docker-compose.yml"
SAMPLE_RULE_FILE = SCRIPT_DIR / "sample_rule.json"
TRIGGER_DOC_FILE = SCRIPT_DIR / "trigger_document.json"
DEFAULT_USER = "elastic"
MAX_KIBANA_WAIT_SECONDS = 180  # 3 minutes
KIBANA_CHECK_INTERVAL_SECONDS = 5
MAX_ALERT_WAIT_SECONDS = 150  # Wait up to 2.5 minutes for signals
ALERT_CHECK_INTERVAL_SECONDS = 10
KIBANA_SYSTEM_USER = "kibana_system_user"
KIBANA_SYSTEM_PASSWORD = "kibanapass" # Hardcoded for simplicity in testing setup
MAX_ES_WAIT_SECONDS = 90  # Wait up to 1.5 minutes for ES
ES_CHECK_INTERVAL_SECONDS = 5

# --- Custom Kibana Role Definition ---
CUSTOM_KIBANA_ROLE_NAME = "kibana_system_role"
CUSTOM_KIBANA_ROLE_PAYLOAD = {
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
        # *** Alerting/Detection Signal Indices (Allow restricted) ***
        # Added .internal.signals* for detection engine signals
        {"names": [".internal.alerts*", ".alerts*", ".preview.alerts*", ".internal.preview.alerts*", ".siem-signals*", ".internal.signals*"], "privileges": ["all"], "allow_restricted_indices": True},
        # Endpoint Metrics/Events (read)
        {"names": ["metrics-endpoint.policy-*", "metrics-endpoint.metrics-*", "logs-endpoint.events.*"], "privileges": ["read"], "allow_restricted_indices": False},
        # Data stream lifecycle management for various logs/metrics/traces
        {"names": ["logs-*", "synthetics-*", "traces-*", "/metrics-.*&~(metrics-endpoint\.metadata_current_default.*)/", ".logs-endpoint.action.responses-*", ".logs-endpoint.diagnostic.collection-*", ".logs-endpoint.actions-*", ".logs-endpoint.heartbeat-*", ".logs-osquery_manager.actions-*", ".logs-osquery_manager.action.responses-*", "profiling-*"], "privileges": ["indices:admin/settings/update", "indices:admin/mapping/put", "indices:admin/rollover", "indices:admin/data_stream/lifecycle/put"], "allow_restricted_indices": False},
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
    "applications": [
         { # Explicitly grant all privileges for the alerts feature
            "application": "alerts",
            "privileges": ["all"],
            "resources": ["*"]
         },
         { # Explicitly grant all privileges for the detections/security feature
            "application": "securitySolution", # Correct application name for Security features
            "privileges": ["all"],
            "resources": ["*"]
         },
         { # Keep broader Kibana access just in case
            "application": "kibana",
            "privileges": ["feature_discover.all", "feature_dashboard.all", "feature_visualize.all", "feature_canvas.all", "feature_maps.all", "feature_logs.all", "feature_infrastructure.all", "feature_uptime.all", "feature_apm.all", "feature_siem.all", "feature_dev_tools.all", "feature_saved_objects_management.all", "feature_advanced_settings.all", "feature_index_patterns.all", "feature_fleet.all" ], # Grant specific features instead of 'all'
            "resources": ["*"]
         }
    ],
    "run_as": [],
    "metadata": {},
    "transient_metadata": {"enabled": True}
} 