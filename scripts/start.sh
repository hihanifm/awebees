#!/bin/bash

# Start script for Awebees frontend and backend
# This script starts both services as background processes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"

# Function to cleanup on exit
cleanup() {
  if [ -f "$PID_FILE" ]; then
    rm -f "$PID_FILE"
  fi
}

trap cleanup EXIT

# Check if processes are already running
if [ -f "$PID_FILE" ]; then
  BACKEND_PID=$(awk '/backend/{print $2}' "$PID_FILE" 2>/dev/null)
  FRONTEND_PID=$(awk '/frontend/{print $2}' "$PID_FILE" 2>/dev/null)
  
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend is already running (PID: $BACKEND_PID)"
    exit 1
  fi
  
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "Frontend is already running (PID: $FRONTEND_PID)"
    exit 1
  fi
fi

echo "Starting Awebees services..."

# Start backend
echo "Starting backend on port 5001..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
  echo "Warning: Python virtual environment not found. Please create one with: python3 -m venv venv"
fi

source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --reload --host 0.0.0.0 --port 5001 > "$SCRIPT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Start frontend
echo "Starting frontend on port 5000..."
cd "$PROJECT_ROOT/frontend"
npm run dev > "$SCRIPT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

# Save PIDs
echo "backend $BACKEND_PID" > "$PID_FILE"
echo "frontend $FRONTEND_PID" >> "$PID_FILE"

echo ""
echo "Services started successfully!"
echo "Backend: http://localhost:5001 (PID: $BACKEND_PID)"
echo "Frontend: http://localhost:5000 (PID: $FRONTEND_PID)"
echo ""
echo "Logs:"
echo "  Backend: $SCRIPT_DIR/backend.log"
echo "  Frontend: $SCRIPT_DIR/frontend.log"
echo ""
echo "Use './scripts/status.sh' to check status"
echo "Use './scripts/stop.sh' to stop services"

