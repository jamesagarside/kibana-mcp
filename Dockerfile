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

# Health check to ensure the server can start (Cloud Run compatible)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port for Cloud Run (uses PORT environment variable)
EXPOSE ${PORT:-8080}

# Set entry point to run the Kibana MCP server
ENTRYPOINT ["uv", "run", "kibana-mcp"]