#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the directory of the script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Run the Python setup script using module execution
cd "$SCRIPT_DIR/.." # Go up one level to the project root
echo "[INFO] Executing Python setup script: python -m testing.seed_data ..."
python3 -m testing.seed_data # Use python3 and run as module

echo "[INFO] Script finished." 