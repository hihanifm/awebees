#!/bin/bash

# Start script for Awebees frontend and backend
# This script starts both services as background processes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"

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

# Load backend environment variables
if [ -f "$PROJECT_ROOT/backend/.env" ]; then
  set -a
  source "$PROJECT_ROOT/backend/.env"
  set +a
fi

# Set backend defaults if not set
BACKEND_PORT=${PORT:-34001}
BACKEND_HOST=${HOST:-0.0.0.0}

# Load frontend environment variables (separate from backend)
if [ -f "$PROJECT_ROOT/frontend/.env.local" ]; then
  FRONTEND_PORT_FROM_ENV=$(grep -v '^#' "$PROJECT_ROOT/frontend/.env.local" | grep "^PORT=" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
fi

# Set frontend defaults if not set
FRONTEND_PORT=${FRONTEND_PORT_FROM_ENV:-34000}

# Start backend
echo "Starting backend on port $BACKEND_PORT..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
  echo "Error: Python virtual environment not found in backend/venv"
  echo "Please run ./scripts/setup.sh first to set up the project"
  exit 1
fi

source venv/bin/activate 2>/dev/null || {
  echo "Error: Failed to activate Python virtual environment"
  exit 1
}

uvicorn app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" > "$SCRIPT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Wait a moment and check if backend started successfully
sleep 2
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "Error: Backend failed to start (PID: $BACKEND_PID)"
  echo "Check backend logs: $SCRIPT_DIR/backend.log"
  tail -20 "$SCRIPT_DIR/backend.log" 2>/dev/null || echo "No logs available"
  exit 1
fi

# Check for common errors in backend logs
if grep -qi "error\|failed\|exception" "$SCRIPT_DIR/backend.log" 2>/dev/null | tail -5; then
  echo "Warning: Backend logs contain errors. Check: $SCRIPT_DIR/backend.log"
fi

echo "Backend started (PID: $BACKEND_PID, Port: $BACKEND_PORT)"

# Start frontend (PORT env var is used by Next.js)
cd "$PROJECT_ROOT/frontend"
# Find npm in PATH - use full path from shell environment
if [ -z "$NPM_CMD" ]; then
  NPM_CMD=$(command -v npm)
  if [ -z "$NPM_CMD" ]; then
    # Try common locations
    if [ -f "/opt/homebrew/bin/npm" ]; then
      NPM_CMD="/opt/homebrew/bin/npm"
    elif [ -f "/usr/local/bin/npm" ]; then
      NPM_CMD="/usr/local/bin/npm"
    else
      echo "Error: npm not found in PATH"
      echo "Please install Node.js and npm, or add npm to your PATH"
      exit 1
    fi
  fi
fi

if [ ! -d "node_modules" ]; then
  echo "Error: Node.js dependencies not found in frontend/node_modules"
  echo "Please run ./scripts/setup.sh first to install dependencies"
  exit 1
fi

PORT=$FRONTEND_PORT "$NPM_CMD" run dev > "$SCRIPT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait a moment and check if frontend started successfully
sleep 3
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "Error: Frontend failed to start (PID: $FRONTEND_PID)"
  echo "Check frontend logs: $SCRIPT_DIR/frontend.log"
  tail -20 "$SCRIPT_DIR/frontend.log" 2>/dev/null || echo "No logs available"
  # Clean up backend if frontend failed
  kill "$BACKEND_PID" 2>/dev/null
  exit 1
fi

# Check for common errors in frontend logs
if grep -qi "error\|failed\|EADDRINUSE" "$SCRIPT_DIR/frontend.log" 2>/dev/null | tail -5; then
  echo "Warning: Frontend logs contain errors. Check: $SCRIPT_DIR/frontend.log"
  # Check specifically for port in use
  if grep -qi "EADDRINUSE" "$SCRIPT_DIR/frontend.log" 2>/dev/null; then
    echo "Error: Port $FRONTEND_PORT is already in use"
    echo "Try changing PORT in frontend/.env.local or stop the process using that port"
    kill "$FRONTEND_PID" 2>/dev/null
    kill "$BACKEND_PID" 2>/dev/null
    exit 1
  fi
fi

# Save PIDs
echo "backend $BACKEND_PID" > "$PID_FILE"
echo "frontend $FRONTEND_PID" >> "$PID_FILE"

echo ""
echo "Services started successfully!"
echo "Backend: http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
echo "Frontend: http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)"
echo ""
echo "Logs:"
echo "  Backend: $SCRIPT_DIR/backend.log"
echo "  Frontend: $SCRIPT_DIR/frontend.log"
echo ""
echo "Use './scripts/status.sh' to check status"
echo "Use './scripts/stop.sh' to stop services"
