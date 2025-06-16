#!/bin/bash
# Script to test GitHub Actions workflow locally using Docker directly

# Ensure we're in the project directory
cd "$(dirname "$0")"

echo "Testing the workflow components locally"
echo "======================================"

echo -e "\nAvailable test options:"
echo "1. Run tests"
echo "2. Build Docker image"
echo "3. Build Docker image for multiple architectures"
echo -e "4. Exit\n"

read -p "Select an option (1-4): " option

case $option in
    1)
        echo -e "\nRunning tests..."
        if [ ! -d ".venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv .venv
        fi
        
        echo "Activating virtual environment..."
        source .venv/bin/activate
        
        echo "Installing dependencies..."
        pip install --upgrade pip
        pip install pytest pytest-cov
        pip install uv
        uv sync
        
        if [ -f testing/requirements-dev.txt ]; then 
            echo "Installing dev requirements..."
            pip install -r testing/requirements-dev.txt
        fi
        
        echo "Running tests..."
        export PYTHONPATH=./src
        pytest -xvs
        ;;
    2)
        echo -e "\nBuilding Docker image..."
        docker build -t kibana-mcp:local .
        echo -e "\nImage built successfully. Available images:"
        docker image ls | grep kibana-mcp
        ;;
    3)
        echo -e "\nSetting up buildx for multi-architecture builds..."
        
        # Create a new builder if it doesn't exist
        if ! docker buildx inspect mybuilder > /dev/null 2>&1; then
            docker buildx create --name mybuilder --use
        else
            docker buildx use mybuilder
        fi
        
        # Bootstrap the builder
        docker buildx inspect --bootstrap
        
        echo -e "\nBuilding multi-architecture image (this will not be pushed)..."
        docker buildx build --platform linux/amd64,linux/arm64 -t kibana-mcp:multiarch --load .
        
        echo -e "\nBuild complete. Available images:"
        docker image ls | grep kibana-mcp
        ;;
    4)
        echo -e "\nExiting..."
        exit 0
        ;;
    *)
        echo -e "\nInvalid option. Please select 1-4."
        exit 1
        ;;
esac

echo -e "\nTask completed."
