#!/bin/bash

# Build script for Windows production packages
# Prepares packages on Linux/Mac before pushing to GitHub
# Usage: ./scripts/build-windows.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist/windows"
BUILD_DIR="$PROJECT_ROOT/build/windows"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Building Windows production packages..."
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

if ! command -v zip &> /dev/null; then
    echo -e "${RED}Error: zip is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Read version from VERSION file
if [ ! -f "$PROJECT_ROOT/VERSION" ]; then
    echo -e "${RED}Error: VERSION file not found${NC}"
    exit 1
fi

VERSION=$(cat "$PROJECT_ROOT/VERSION" | tr -d '[:space:]')
echo "Version: $VERSION"
echo ""

# Build frontend
echo "Building frontend..."
cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Warning: node_modules not found. Installing dependencies...${NC}"
    npm install
fi

npm run build

if [ ! -d "out" ]; then
    echo -e "${RED}Error: Frontend build failed. 'out' directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend built successfully${NC}"
echo ""

# Create build directories
echo "Preparing build directories..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

echo -e "${GREEN}✓ Build directories created${NC}"
echo ""

# Prepare both package variants
echo "Preparing packages..."
"$SCRIPT_DIR/windows/prepare-package.sh" "with-python" "$VERSION" "$BUILD_DIR" "$DIST_DIR"
"$SCRIPT_DIR/windows/prepare-package.sh" "requires-python" "$VERSION" "$BUILD_DIR" "$DIST_DIR"

echo ""
echo -e "${GREEN}✓ Windows packages prepared successfully!${NC}"
echo ""
echo "Packages created in: $DIST_DIR"
echo "  - lens-package-with-python-${VERSION}.zip"
echo "  - lens-package-requires-python-${VERSION}.zip"
echo ""
echo "Next steps:"
echo "  1. Review the packages"
echo "  2. Commit and push to GitHub"
echo "  3. Trigger GitHub Actions workflow to create installers"
echo ""

