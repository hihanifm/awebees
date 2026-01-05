#!/bin/bash

# Script to run Python code with cProfile profiling
# Usage: ./run_python.sh <python_script> [args...]
#   -p, --profile: Enable profiling (default: enabled)
#   -n, --no-profile: Disable profiling
#   -t, --top N: Show top N consumers (default: 10)
#   -s, --sort SORT: Sort by 'cumulative' or 'tottime' (default: cumulative)
#   -h, --help: Show help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
PROFILE=true
TOP_N=10
SORT_BY="cumulative"

# Parse arguments
PYTHON_ARGS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--profile)
      PROFILE=true
      shift
      ;;
    -n|--no-profile)
      PROFILE=false
      shift
      ;;
    -t|--top)
      TOP_N="$2"
      shift 2
      ;;
    -s|--sort)
      SORT_BY="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [options] <python_script> [script_args...]"
      echo ""
      echo "Options:"
      echo "  -p, --profile          Enable profiling (default)"
      echo "  -n, --no-profile       Disable profiling"
      echo "  -t, --top N            Show top N CPU consumers (default: 10)"
      echo "  -s, --sort SORT        Sort by 'cumulative' or 'tottime' (default: cumulative)"
      echo "  -h, --help             Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0 -t 20 -s tottime app/main.py"
      echo "  $0 --no-profile app/main.py"
      echo "  $0 -m app.insights.error_detector /path/to/file.log"
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
    *)
      PYTHON_ARGS+=("$1")
      shift
      ;;
  esac
done

# Check if Python script is provided
if [ ${#PYTHON_ARGS[@]} -eq 0 ]; then
  echo "Error: No Python script or module provided"
  echo "Use -h or --help for usage information"
  exit 1
fi

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/backend/venv" ]; then
  source "$PROJECT_ROOT/backend/venv/bin/activate"
fi

# Set PYTHONPATH to include backend directory for module imports
export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"

# Run with or without profiling
if [ "$PROFILE" = true ]; then
  echo "Running with cProfile profiling (top $TOP_N consumers, sorted by $SORT_BY)..."
  echo ""
  
  # Create temporary profile file (mktemp needs exactly 6 X's, creates absolute path)
  # Use a unique filename with process ID to avoid conflicts
  PROFILE_FILE="/tmp/python_profile_$$_$(date +%s).prof"
  
  # Use Python wrapper to avoid cProfile argument parsing issues
  python3 "$SCRIPT_DIR/_run_with_profile.py" "$PROFILE_FILE" "$SORT_BY" "$TOP_N" "${PYTHON_ARGS[@]}"
  EXIT_CODE=$?
  
  if [ $EXIT_CODE -ne 0 ]; then
    echo "Error: Python script exited with code $EXIT_CODE"
    rm -f "$PROFILE_FILE"
    exit $EXIT_CODE
  fi
else
  # Run without profiling
  python3 "${PYTHON_ARGS[@]}"
  exit $?
fi

