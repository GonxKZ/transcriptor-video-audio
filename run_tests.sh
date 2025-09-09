#!/bin/bash
# Test runner script for the Transcriptor application

echo "Running Transcriptor tests..."

# Activate virtual environment
source .venv/bin/activate

# Run basic tests
echo "Running basic tests..."
python -m pytest tests/test_basic.py -v

echo "Tests completed."