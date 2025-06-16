start-test-env:
	@echo "Setting up test environment with Fleet Server and Elastic Agent..."
	@python -m venv .venv
	@. .venv/bin/activate && pip install -r ./testing/requirements-dev.txt
	@./testing/quickstart-test-env.sh


stop-test-env:
	@echo "Stopping test environment..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose -f "./testing/docker-compose.yml" down; \
	else \
		docker compose -f "./testing/docker-compose.yml" down; \
	fi

start-endpoint-env:
	@echo "Starting endpoint test environment with Fleet Server and Agent..."
	@./testing/start-endpoint-test-env.sh

dev:
	uv sync && \
	KIBANA_URL="http://localhost:5601" \
	KIBANA_USERNAME="elastic" \
	KIBANA_PASSWORD="elastic" \
	uv run kibana-mcp

load_venv:
	@python -m venv .venv
	@echo "Activating virtual environment..."
	@. .venv/bin/activate
	@echo "Installing dependencies..."
	@pip install -r ./testing/requirements-dev.txt

run_coverage_test: load_venv
	@echo "Running coverage tests..."
	@export PYTHONPATH=./src pytest
	@coverage run -m pytest
	@coverage report -m
	@coverage html

run_pytest: load_venv
	@echo "Running pytest..."
	@PYTHONPATH=./src pytest -xvs testing/tools/test_all.py

test:	run_pytest run_coverage_test

build: 
	@echo "Building the project..."
	@docker build -t kibana-mcp .