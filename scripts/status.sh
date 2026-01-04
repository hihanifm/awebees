#!/bin/bash

# Status script for Awebees frontend and backend
# This script checks if the services are running

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"

if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found. Services are not running (or were not started with start.sh)."
  exit 0
fi

BACKEND_PID=$(awk '/backend/{print $2}' "$PID_FILE" 2>/dev/null)
FRONTEND_PID=$(awk '/frontend/{print $2}' "$PID_FILE" 2>/dev/null)

echo "Awebees Services Status"
echo "======================"
echo ""

# Check backend
if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "✓ Backend: RUNNING (PID: $BACKEND_PID, Port: 5001)"
else
  echo "✗ Backend: NOT RUNNING"
fi

# Check frontend
if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "✓ Frontend: RUNNING (PID: $FRONTEND_PID, Port: 5000)"
else
  echo "✗ Frontend: NOT RUNNING"
fi

echo ""

