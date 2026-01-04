#!/bin/bash

# Stop script for Lens frontend and backend
# This script stops both services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"

if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found. Services are not running (or were not started with start.sh)."
  exit 0
fi

BACKEND_PID=$(awk '/backend/{print $2}' "$PID_FILE" 2>/dev/null)
FRONTEND_PID=$(awk '/frontend/{print $2}' "$PID_FILE" 2>/dev/null)

echo "Stopping Lens services..."

# Stop backend
if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "Stopping backend (PID: $BACKEND_PID)..."
  kill "$BACKEND_PID" 2>/dev/null
  # Wait a bit and force kill if needed
  sleep 1
  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill -9 "$BACKEND_PID" 2>/dev/null
  fi
  echo "Backend stopped"
else
  echo "Backend was not running"
fi

# Stop frontend
if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "Stopping frontend (PID: $FRONTEND_PID)..."
  kill "$FRONTEND_PID" 2>/dev/null
  # Wait a bit and force kill if needed
  sleep 1
  if kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill -9 "$FRONTEND_PID" 2>/dev/null
  fi
  echo "Frontend stopped"
else
  echo "Frontend was not running"
fi

# Cleanup PID file
rm -f "$PID_FILE"
echo ""
echo "All services stopped."

