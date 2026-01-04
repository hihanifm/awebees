#!/bin/bash

# View logs script for Awebees
# Shows the last 20 lines of frontend or backend logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"

# Default to frontend if no argument provided
SHOW_FRONTEND=true
SHOW_BACKEND=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -f|--frontend)
      SHOW_FRONTEND=true
      SHOW_BACKEND=false
      shift
      ;;
    -b|--backend)
      SHOW_FRONTEND=false
      SHOW_BACKEND=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [-f|--frontend] [-b|--backend]"
      echo ""
      echo "Options:"
      echo "  -f, --frontend  Show frontend logs (default)"
      echo "  -b, --backend   Show backend logs"
      echo "  -h, --help      Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Show logs
if [ "$SHOW_FRONTEND" = true ]; then
  if [ -f "$FRONTEND_LOG" ]; then
    echo "=== Frontend Logs (last 20 lines) ==="
    echo "File: $FRONTEND_LOG"
    echo ""
    tail -20 "$FRONTEND_LOG"
  else
    echo "Frontend log file not found: $FRONTEND_LOG"
    exit 1
  fi
elif [ "$SHOW_BACKEND" = true ]; then
  if [ -f "$BACKEND_LOG" ]; then
    echo "=== Backend Logs (last 20 lines) ==="
    echo "File: $BACKEND_LOG"
    echo ""
    tail -20 "$BACKEND_LOG"
  else
    echo "Backend log file not found: $BACKEND_LOG"
    exit 1
  fi
fi

