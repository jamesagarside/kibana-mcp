###############################################################################
# Kibana MCP Server - Makefile
###############################################################################

# Version variables
ELASTIC_PACKAGE_VERSION := 0.112.0
ELASTICSEARCH_STACK_VERSION := 8.18.2
DOCKER_IMAGE_NAME := kibana-mcp

# Directories
SRC_DIR := ./src
TEST_DIR := ./testing
VENV_DIR := .venv

# Default target
.PHONY: help
help:
	@echo "Kibana MCP Server - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  help                   - Show this help message"
	@echo "  dev                    - Run the server locally in development mode"
	@echo "  build                  - Build the Docker image"
	@echo ""
	@echo "Testing:"
	@echo "  test                   - Run all tests (pytest and coverage)"
	@echo "  run-pytest             - Run pytest only"
	@echo "  run-coverage           - Run tests with coverage reporting"
	@echo ""
	@echo "Test Environment:"
	@echo "  install-elastic-package - Install the elastic-package tool"
	@echo "  start-test-env         - Start the complete test environment"
	@echo "  start-elastic-stack    - Start only the Elastic Stack containers"
	@echo "  configure-test-env     - Configure the test environment"
	@echo "  stop-test-env          - Stop the test environment"

###############################################################################
# Development targets
###############################################################################

.PHONY: dev
dev: ## Run the server locally in development mode
	@echo "Starting kibana-mcp in development mode..."
	uv sync && \
	KIBANA_URL="http://localhost:5601" \
	KIBANA_USERNAME="elastic" \
	KIBANA_PASSWORD="elastic" \
	uv run kibana-mcp

.PHONY: build
build: ## Build the Docker image
	@echo "Building Docker image $(DOCKER_IMAGE_NAME)..."
	docker build -t $(DOCKER_IMAGE_NAME) .
	@echo "Build complete: $(DOCKER_IMAGE_NAME)"

###############################################################################
# Testing targets
###############################################################################

.PHONY: load-venv
load-venv: ## Create and initialize virtual environment
	@echo "Creating and activating virtual environment..."
	@python -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	@. $(VENV_DIR)/bin/activate && pip install -r $(TEST_DIR)/requirements-dev.txt
	@echo "Virtual environment ready at $(VENV_DIR)"

.PHONY: run-pytest
run-pytest: load-venv ## Run pytest only
	@echo "Running pytest..."
	@. $(VENV_DIR)/bin/activate && PYTHONPATH=$(SRC_DIR) pytest -xvs $(TEST_DIR)/tools/test_all.py

.PHONY: run-coverage
run-coverage: load-venv ## Run tests with coverage reporting
	@echo "Running tests with coverage..."
	@. $(VENV_DIR)/bin/activate && PYTHONPATH=$(SRC_DIR) pytest
	@. $(VENV_DIR)/bin/activate && PYTHONPATH=$(SRC_DIR) coverage run -m pytest
	@. $(VENV_DIR)/bin/activate && coverage report -m
	@. $(VENV_DIR)/bin/activate && coverage html
	@echo "Coverage report generated in htmlcov/"

.PHONY: test
test: run-pytest run-coverage ## Run all tests (pytest and coverage)
	@echo "All tests completed"

###############################################################################
# Test environment targets
###############################################################################

.PHONY: install-elastic-package
install-elastic-package: ## Install the elastic-package tool
	@echo "Installing elastic-package v$(ELASTIC_PACKAGE_VERSION)..."
	@ARCH=$$(uname -m); \
	if [ "$$ARCH" = "x86_64" ]; then \
		ARCH="amd64"; \
	elif [ "$$ARCH" = "arm64" ]; then \
		ARCH="arm64"; \
	else \
		echo "Error: Unsupported architecture: $$ARCH"; \
		exit 1; \
	fi; \
	OS=$$(uname -s | tr '[:upper:]' '[:lower:]'); \
	if [ "$$OS" = "darwin" ]; then \
		OS="darwin"; \
	elif [ "$$OS" = "linux" ]; then \
		OS="linux"; \
	else \
		echo "Error: Unsupported OS: $$OS"; \
		exit 1; \
	fi; \
	URL="https://github.com/elastic/elastic-package/releases/download/v$(ELASTIC_PACKAGE_VERSION)/elastic-package_$(ELASTIC_PACKAGE_VERSION)_$${OS}_$${ARCH}.tar.gz"; \
	echo "Detected OS: $$OS, Architecture: $$ARCH"; \
	echo "Downloading from $$URL..."; \
	TMPDIR=$$(mktemp -d); \
	curl -L $$URL -o $$TMPDIR/elastic-package.tar.gz && \
	if [ ! -s $$TMPDIR/elastic-package.tar.gz ]; then \
		echo "Error: Downloaded file is empty or failed to download."; \
		rm -rf $$TMPDIR; \
		exit 1; \
	fi && \
	tar -xzf $$TMPDIR/elastic-package.tar.gz -C $$TMPDIR && \
	cp $$TMPDIR/elastic-package $(TEST_DIR)/ && \
	chmod +x $(TEST_DIR)/elastic-package && \
	rm -rf $$TMPDIR && \
	echo "elastic-package installed to $(TEST_DIR)/elastic-package"

.PHONY: configure-test-env
configure-test-env: ## Configure the test environment
	@echo "Setting up test environment with Fleet Server and Elastic Agent..."
	@python -m venv $(VENV_DIR)
	@. $(VENV_DIR)/bin/activate && pip install -r $(TEST_DIR)/requirements-dev.txt
	@$(TEST_DIR)/quickstart-test-env.sh

.PHONY: start-elastic-stack
start-elastic-stack: ## Start the Elastic Stack containers
	@echo "Starting Elastic Stack with version $(ELASTICSEARCH_STACK_VERSION)..."
	@echo "This may take a few minutes..."
	@if [ ! -f "$(TEST_DIR)/elastic-package" ]; then \
		echo "Error: elastic-package not found. Please run 'make install-elastic-package' first"; \
		exit 1; \
	fi
	@$(TEST_DIR)/elastic-package stack up --version $(ELASTICSEARCH_STACK_VERSION) -d

.PHONY: start-test-env
start-test-env: start-elastic-stack configure-test-env ## Start the complete test environment
	@echo "Test environment is ready!"

.PHONY: stop-test-env
stop-test-env: ## Stop the test environment
	@echo "Stopping Elastic Stack test environment..."
	@if [ ! -f "$(TEST_DIR)/elastic-package" ]; then \
		echo "Error: elastic-package not found. The environment may not be running."; \
		exit 1; \
	fi
	@$(TEST_DIR)/elastic-package stack down
	@echo "Test environment stopped"