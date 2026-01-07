#!/bin/bash

# Setup script for Lens - Run this once before starting services
# This script sets up the Python virtual environment, installs dependencies,
# and creates .env files from examples

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Setting up Lens..."
echo ""

# Setup Backend
echo "=== Backend Setup ==="
cd "$PROJECT_ROOT/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
  echo "Virtual environment created in backend/venv"
else
  echo "Virtual environment already exists in backend/venv"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "Python dependencies installed"
deactivate

# Create .env file from .env.example if it doesn't exist
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Created backend/.env from .env.example"
  else
    echo "Warning: .env.example not found, creating basic .env file"
    cat > .env << EOF
PORT=5001
HOST=0.0.0.0
FRONTEND_URL=http://localhost:5000
LOG_LEVEL=INFO
EOF
    echo "Created basic backend/.env file"
  fi
else
  echo "backend/.env already exists, skipping"
fi

echo ""

# Setup Frontend
echo "=== Frontend Setup ==="
cd "$PROJECT_ROOT/frontend"

# Install/update npm dependencies
echo "Installing/updating Node.js dependencies..."
npm install
echo "Node.js dependencies installed"

# Create .env.local file from .env.example if it doesn't exist
if [ ! -f ".env.local" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env.local
    echo "Created frontend/.env.local from .env.example"
  else
    echo "Warning: .env.example not found, creating basic .env.local file"
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:5001
PORT=5000
EOF
    echo "Created basic frontend/.env.local file"
  fi
else
  echo "frontend/.env.local already exists, skipping"
fi

echo ""

# Check and install ripgrep
echo "=== Optional Tools ==="
echo "Checking for ripgrep..."
if ! command -v rg &> /dev/null; then
    echo "ripgrep not found. Installing for 10-100x faster pattern matching..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ripgrep
            echo "✓ ripgrep installed via Homebrew"
        else
            echo "⚠ Homebrew not found. Please install ripgrep manually:"
            echo "  brew install ripgrep"
            echo "  Or visit: https://github.com/BurntSushi/ripgrep#installation"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y ripgrep
            echo "✓ ripgrep installed via apt"
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y ripgrep
            echo "✓ ripgrep installed via dnf"
        elif command -v pacman &> /dev/null; then
            sudo pacman -S ripgrep
            echo "✓ ripgrep installed via pacman"
        else
            echo "⚠ Package manager not detected. Please install ripgrep manually:"
            echo "  https://github.com/BurntSushi/ripgrep#installation"
        fi
    else
        echo "⚠ Unsupported OS. Please install ripgrep manually:"
        echo "  https://github.com/BurntSushi/ripgrep#installation"
    fi
else
    echo "✓ ripgrep is already installed ($(rg --version | head -1))"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "You can now start the services with:"
echo "  ./scripts/start.sh"
echo ""
echo "Or check status with:"
echo "  ./scripts/status.sh"

