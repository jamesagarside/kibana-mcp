#!/bin/bash
# Script to test GitHub Actions workflow locally

# Set executable permissions
chmod +x "$0"

echo "Testing GitHub Actions workflow locally using 'act'"
echo "=================================================="

# Test options
echo -e "\nAvailable test options:"
echo "1. Run tests only"
echo "2. Build Docker image only (no push)"
echo "3. Run full workflow (tests + build)"
echo "4. List jobs without running"
echo -e "5. Exit\n"

# Ask for user input
read -p "Select an option (1-5): " option

case $option in
    1)
        echo -e "\nRunning tests job only..."
        act -j test --reuse
        ;;
    2)
        echo -e "\nBuilding Docker image only (without pushing)..."
        act -j build-and-push --reuse
        ;;
    3)
        echo -e "\nRunning full workflow (tests + build)..."
        act --reuse
        ;;
    4)
        echo -e "\nListing available jobs without running..."
        act -l
        ;;
    5)
        echo -e "\nExiting..."
        exit 0
        ;;
    *)
        echo -e "\nInvalid option. Please select 1-5."
        exit 1
        ;;
esac

echo -e "\nJob completed."
