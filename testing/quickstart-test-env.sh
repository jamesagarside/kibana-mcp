#!/bin/bash

# Simple wrapper to execute the Python-based test environment setup script.

set -e

# Determine the directory where this script resides
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PYTHON_SCRIPT="$SCRIPT_DIR/seed_data.py"

# Check if Python 3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 command not found. Please ensure Python 3 is installed and in your PATH." >&2
    exit 1
fi

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "[ERROR] Setup script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Execute the Python script
echo "[INFO] Executing Python setup script: $PYTHON_SCRIPT ..."
python3 "$PYTHON_SCRIPT"

exit $? # Exit with the same status code as the Python script 