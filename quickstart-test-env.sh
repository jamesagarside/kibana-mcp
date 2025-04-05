#!/bin/bash

# Script to quickly start the Kibana/Elasticsearch test environment

set -e # Exit immediately if a command exits with a non-zero status.

COMPOSE_FILE="docker-compose.yml"
DEFAULT_USER="elastic"

# --- Helper Functions ---
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# --- Pre-flight Checks ---
echo "[INFO] Checking prerequisites..."

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "[ERROR] $COMPOSE_FILE not found in the current directory." >&2
    exit 1
fi

if ! command_exists docker; then
    echo "[ERROR] Docker is not installed or not in PATH. Please install Docker: https://docs.docker.com/get-docker/" >&2
    exit 1
fi

# Check for Docker Compose (v1 or v2)
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
     echo "[ERROR] Docker Compose (v1 'docker-compose' or v2 'docker compose') is not installed or not available." >&2
     echo "Please install Docker Compose: https://docs.docker.com/compose/install/" >&2
     exit 1
fi

# Use docker compose if available (v2), otherwise fallback to docker-compose (v1)
DOCKER_COMPOSE_CMD="docker-compose"
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "[INFO] Using Docker Compose V2 ('docker compose')."
else
    echo "[INFO] Using Docker Compose V1 ('docker-compose')."
fi

# --- Extract Information ---n# Attempt to extract info directly from docker-compose.yml to be more dynamic
ES_PORT=$(grep -A 5 'elasticsearch:' "$COMPOSE_FILE" | grep 'ports:' -A 1 | grep -Eo '[0-9]+:9200' | cut -d: -f1 | tr -d '"' | tr -d ' ' || echo "9200") # Default fallback
KIBANA_PORT=$(grep -A 8 'kibana:' "$COMPOSE_FILE" | grep 'ports:' -A 1 | grep -Eo '[0-9]+:5601' | cut -d: -f1 | tr -d '"' | tr -d ' ' || echo "5601") # Default fallback
ES_PASSWORD=$(grep -A 5 'elasticsearch:' "$COMPOSE_FILE" | grep 'ELASTIC_PASSWORD=' | sed 's/.*ELASTIC_PASSWORD=//' | sed 's/#.*//' | tr -d ' ' | tr -d '"' || echo "elastic") # Default fallback

# --- Start Services ---
echo "[INFO] Starting Elasticsearch and Kibana using Docker Compose..."
$DOCKER_COMPOSE_CMD up -d

if [ $? -ne 0 ]; then
    echo "[ERROR] Docker Compose failed to start the services." >&2
    echo "Check the output above for details. You might need to run '$DOCKER_COMPOSE_CMD up' without '-d' to see logs." >&2
    exit 1
fi

# --- Output Information ---
echo ""
echo "-----------------------------------------------------"
echo " Elasticsearch & Kibana Quickstart Initiated!"
echo "-----------------------------------------------------"
echo ""
echo "Services are starting in the background."
echo "It might take a minute or two for them to be fully ready (due to healthchecks)."
echo "You can check the status with: $DOCKER_COMPOSE_CMD ps"
echo "You can view logs with:       $DOCKER_COMPOSE_CMD logs -f"
echo ""
echo "Access Details:"
echo " -> Elasticsearch: http://localhost:$ES_PORT"
echo " -> Kibana:        http://localhost:$KIBANA_PORT"
echo ""
echo "Credentials:"
echo " -> Username: $DEFAULT_USER"
echo " -> Password: $ES_PASSWORD (from $COMPOSE_FILE)"
echo ""
echo "To stop the services, run: $DOCKER_COMPOSE_CMD down"
echo "-----------------------------------------------------"

exit 0 