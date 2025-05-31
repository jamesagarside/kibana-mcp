FROM python:3.11-slim

LABEL maintainer="George Gilligan <ggilligan12@gmail.com>"
LABEL description="Kibana MCP Server - Model Context Protocol server for Kibana Security functions"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files, README, and source code (all needed for uv sync)
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies using uv
RUN uv sync --frozen

# Set Python path to include src directory
ENV PYTHONPATH=/app/src

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash kibana && \
    chown -R kibana:kibana /app
USER kibana

# Health check to ensure the server can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from kibana_mcp.server import configure_http_client; print('Health check passed')" || exit 1

# Expose no specific port since MCP uses stdio
EXPOSE 8080

# Set entry point to run the Kibana MCP server
ENTRYPOINT ["uv", "run", "kibana-mcp"]