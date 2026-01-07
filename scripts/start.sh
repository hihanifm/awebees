#!/bin/bash

# Start script for Lens frontend and backend
# This script starts both services as background processes
# Usage: ./start.sh [-p] [-h]
#   -p: Production mode (uses next start instead of next dev)
#   -h: Show help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"
LOGS_DIR="$PROJECT_ROOT/logs"
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"

# Detect OS
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
  OS_TYPE="Windows"
  OS_DETAILS="Windows (Git Bash/Cygwin)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS_TYPE="macOS"
  OS_DETAILS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS_TYPE="Linux"
  OS_DETAILS="Linux"
else
  OS_TYPE="Unknown"
  OS_DETAILS="$OSTYPE"
fi

# Print OS information
echo "=========================================="
echo "Lens Start Script"
echo "=========================================="
echo "OS: $OS_DETAILS"
echo "OSTYPE: $OSTYPE"
echo "Project Root: $PROJECT_ROOT"
echo "Script Dir: $SCRIPT_DIR"
echo "=========================================="
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Parse arguments
MODE="dev"
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--prod|--production)
      MODE="prod"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [-p|--prod] [-h|--help]"
      echo ""
      echo "Options:"
      echo "  -p, --prod, --production  Start in production mode (default: development)"
      echo "  -h, --help                Show this help message"
      echo ""
      echo "Modes:"
      echo "  Development (default): Uses 'next dev' for frontend with hot reload"
      echo "  Production (-p):       Uses 'next start' for frontend (requires build first)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Set NODE_ENV for Next.js (must be "development" or "production")
if [ "$MODE" = "prod" ]; then
  export NODE_ENV="production"
else
  export NODE_ENV="development"
fi

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

MODE_UPPER=$(echo "$MODE" | tr '[:lower:]' '[:upper:]')
echo "Starting Lens services in $MODE_UPPER mode..."

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

# Function to activate Python virtual environment (cross-platform)
activate_venv() {
  local venv_dir="$1"
  # Try Windows path first (Git Bash on Windows)
  if [ -f "$venv_dir/Scripts/activate" ]; then
    echo "  → Activating venv (Windows path: $venv_dir/Scripts/activate)"
    source "$venv_dir/Scripts/activate" 2>/dev/null && return 0
  fi
  # Try Unix path (Linux/Mac)
  if [ -f "$venv_dir/bin/activate" ]; then
    echo "  → Activating venv (Unix path: $venv_dir/bin/activate)"
    source "$venv_dir/bin/activate" 2>/dev/null && return 0
  fi
  return 1
}

# Start backend
echo "Starting backend..."
echo "  → Host: $BACKEND_HOST"
echo "  → Port: $BACKEND_PORT"
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
  echo "Error: Python virtual environment not found in backend/venv"
  echo "Please run ./scripts/setup.sh first to set up the project"
  exit 1
fi

echo "  → Activating Python virtual environment..."
activate_venv "venv" || {
  echo "Error: Failed to activate Python virtual environment"
  echo "Tried: venv/Scripts/activate (Windows) and venv/bin/activate (Unix)"
  exit 1
}

# Log Python version
PYTHON_VERSION=$(python --version 2>&1 || echo "unknown")
echo "  → Python: $PYTHON_VERSION"

# In production, we'll restart backend after building frontend
# In development, start backend normally
if [ "$MODE" != "prod" ]; then
  uvicorn app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" > "$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
else
  # In production, backend will be started after frontend build
  # Just set a placeholder for now
  BACKEND_PID=""
fi

# Wait a moment and check if backend started successfully (only in dev mode)
if [ "$MODE" != "prod" ]; then
  sleep 2
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Error: Backend failed to start (PID: $BACKEND_PID)"
    echo "Check backend logs: $BACKEND_LOG"
    tail -20 "$BACKEND_LOG" 2>/dev/null || echo "No logs available"
    exit 1
  fi
  
  # Check for common errors in backend logs (only check recent lines to avoid false positives)
  if tail -50 "$BACKEND_LOG" 2>/dev/null | grep -qi "error\|failed\|exception" >/dev/null 2>&1; then
    echo "Warning: Backend logs contain errors. Check: $BACKEND_LOG"
  fi
  
  echo "Backend started (PID: $BACKEND_PID, Port: $BACKEND_PORT)"
fi

# Start frontend
echo ""
echo "Starting frontend..."
echo "  → Port: $FRONTEND_PORT"
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

# Log npm and node versions
NPM_VERSION=$(npm --version 2>&1 || echo "unknown")
NODE_VERSION=$(node --version 2>&1 || echo "unknown")
echo "  → npm: $NPM_VERSION"
echo "  → node: $NODE_VERSION"
echo "  → npm path: $NPM_CMD"

if [ ! -d "node_modules" ]; then
  echo "Error: Node.js dependencies not found in frontend/node_modules"
  echo "Please run ./scripts/setup.sh first to install dependencies"
  exit 1
fi

# Ensure PATH includes node binary location for npm to work
NODE_DIR=$(dirname "$NPM_CMD")
export PATH="$NODE_DIR:$PATH"

# Handle frontend based on mode
if [ "$MODE" = "prod" ]; then
  # Production mode: Build frontend and serve from backend
  echo "Building frontend for production..."
  if [ ! -d "node_modules" ]; then
    echo "Error: Node.js dependencies not found in frontend/node_modules"
    echo "Please run ./scripts/setup.sh first to install dependencies"
    kill "$BACKEND_PID" 2>/dev/null
    exit 1
  fi
  
  # Build frontend (creates frontend/out directory)
  "$NPM_CMD" run build
  BUILD_EXIT_CODE=$?
  
  if [ $BUILD_EXIT_CODE -ne 0 ]; then
    echo "Error: Frontend build failed"
    kill "$BACKEND_PID" 2>/dev/null
    exit 1
  fi
  
  if [ ! -d "out" ]; then
    echo "Error: Frontend build output not found. Expected 'out' directory."
    kill "$BACKEND_PID" 2>/dev/null
    exit 1
  fi
  
  echo "Frontend built successfully"
  
  # Set environment variable to enable frontend serving in backend
  export SERVE_FRONTEND=true
  
  # Start backend with SERVE_FRONTEND enabled (no need to kill, it wasn't started yet)
  cd "$PROJECT_ROOT/backend"
  activate_venv "venv" || {
    echo "Error: Failed to activate Python virtual environment"
    exit 1
  }
  
  SERVE_FRONTEND=true uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" > "$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  
  # Wait and verify backend restarted
  sleep 2
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Error: Backend failed to restart with frontend serving (PID: $BACKEND_PID)"
    echo "Check backend logs: $BACKEND_LOG"
    tail -20 "$BACKEND_LOG" 2>/dev/null || echo "No logs available"
    exit 1
  fi
  
  # Save PIDs (only backend in production)
  echo "backend $BACKEND_PID" > "$PID_FILE"
  
  echo ""
  echo "Services started successfully in PRODUCTION mode!"
  echo "Backend (serving API + Frontend): http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
  echo ""
  echo "Logs:"
  echo "  Backend: $BACKEND_LOG"
  echo ""
  echo "Use './scripts/status.sh' to check status"
  echo "Use './scripts/stop.sh' to stop services"
else
  # Development mode: Start separate frontend server
  echo "Starting frontend in DEVELOPMENT mode on port $FRONTEND_PORT..."
  FRONTEND_CMD="dev"
  
  PORT=$FRONTEND_PORT "$NPM_CMD" run $FRONTEND_CMD > "$FRONTEND_LOG" 2>&1 &
  FRONTEND_PID=$!
  
  # Wait a moment and check if frontend started successfully
  sleep 3
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "Error: Frontend failed to start (PID: $FRONTEND_PID)"
    echo "Check frontend logs: $FRONTEND_LOG"
    tail -20 "$FRONTEND_LOG" 2>/dev/null || echo "No logs available"
    # Clean up backend if frontend failed
    kill "$BACKEND_PID" 2>/dev/null
    exit 1
  fi
  
  # Check for common errors in frontend logs (only check recent lines to avoid false positives)
  if tail -50 "$FRONTEND_LOG" 2>/dev/null | grep -qi "error\|failed\|EADDRINUSE" >/dev/null 2>&1; then
    # Check specifically for port in use (critical error)
    if tail -50 "$FRONTEND_LOG" 2>/dev/null | grep -qi "EADDRINUSE" >/dev/null 2>&1; then
      echo "Error: Port $FRONTEND_PORT is already in use"
      echo "Try changing PORT in frontend/.env.local or stop the process using that port"
      kill "$FRONTEND_PID" 2>/dev/null
      kill "$BACKEND_PID" 2>/dev/null
      exit 1
    fi
    echo "Warning: Frontend logs contain errors. Check: $FRONTEND_LOG"
  fi
  
  # Save PIDs
  echo "backend $BACKEND_PID" > "$PID_FILE"
  echo "frontend $FRONTEND_PID" >> "$PID_FILE"
  
  echo ""
  echo "Services started successfully in DEVELOPMENT mode!"
  echo "Backend: http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
  echo "Frontend: http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)"
  echo ""
  echo "Logs:"
  echo "  Backend: $BACKEND_LOG"
  echo "  Frontend: $FRONTEND_LOG"
  echo ""
  echo "Use './scripts/status.sh' to check status"
  echo "Use './scripts/stop.sh' to stop services"
fi
