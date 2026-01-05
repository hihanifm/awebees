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

# Run with or without profiling
if [ "$PROFILE" = true ]; then
  echo "Running with cProfile profiling (top $TOP_N consumers, sorted by $SORT_BY)..."
  echo ""
  
  # Create temporary profile file
  PROFILE_FILE=$(mktemp /tmp/python_profile_XXXXXX.prof)
  
  # Run with cProfile
  python3 -m cProfile -s "$SORT_BY" -o "$PROFILE_FILE" "${PYTHON_ARGS[@]}"
  EXIT_CODE=$?
  
  if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Profile results (top $TOP_N consumers, sorted by $SORT_BY):"
    echo "============================================================"
    python3 -c "
import pstats
stats = pstats.Stats('$PROFILE_FILE')
stats.sort_stats('$SORT_BY')
stats.print_stats($TOP_N)
"
    echo ""
    echo "Full profile saved to: $PROFILE_FILE"
    echo "To view full profile: python3 -m pstats $PROFILE_FILE"
  else
    echo "Error: Python script exited with code $EXIT_CODE"
    rm -f "$PROFILE_FILE"
    exit $EXIT_CODE
  fi
else
  # Run without profiling
  python3 "${PYTHON_ARGS[@]}"
  exit $?
fi

