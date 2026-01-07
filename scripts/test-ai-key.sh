#!/bin/bash
# Test OpenAI API key and connection for Lens
# Usage: ./scripts/test-ai-key.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Use the virtual environment's Python
PYTHON="$PROJECT_ROOT/backend/venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Error: Virtual environment not found"
    echo ""
    echo "Please run setup first:"
    echo "  ./scripts/setup.sh"
    exit 1
fi

# Run the test script
"$PYTHON" "$SCRIPT_DIR/test-ai-key.py" "$@"

