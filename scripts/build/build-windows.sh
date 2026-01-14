#!/bin/bash

# Build script for Windows production packages
# Prepares packages on Linux/Mac before pushing to GitHub
# Usage: ./scripts/build/build-windows.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
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

# Update docs/index.html with new version
echo "Updating download page (docs/index.html)..."
DOCS_INDEX="$PROJECT_ROOT/docs/index.html"
if [ -f "$DOCS_INDEX" ]; then
    # Use sed to update version in all occurrences
    # macOS and Linux sed have different syntax, so we use a temp file approach
    sed "s/Version [0-9]\+\.[0-9]\+\.[0-9]\+/Version $VERSION/g" "$DOCS_INDEX" > "$DOCS_INDEX.tmp"
    sed "s|/v[0-9]\+\.[0-9]\+\.[0-9]\+/|/v$VERSION/|g" "$DOCS_INDEX.tmp" > "$DOCS_INDEX.tmp2"
    sed "s/lens-setup-requires-python-[0-9]\+\.[0-9]\+\.[0-9]\+\.exe/lens-setup-requires-python-$VERSION.exe/g" "$DOCS_INDEX.tmp2" > "$DOCS_INDEX.tmp3"
    sed "s/lens-setup-with-python-[0-9]\+\.[0-9]\+\.[0-9]\+\.exe/lens-setup-requires-python-$VERSION.exe/g" "$DOCS_INDEX.tmp3" > "$DOCS_INDEX"
    rm -f "$DOCS_INDEX.tmp3"
    rm -f "$DOCS_INDEX.tmp" "$DOCS_INDEX.tmp2"
    echo -e "${GREEN}✓ Download page updated to version $VERSION${NC}"
else
    echo -e "${YELLOW}Warning: docs/index.html not found, skipping update${NC}"
fi
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

# Remove old ZIP files to prevent duplication issues
echo "Cleaning old packages..."
rm -f "$DIST_DIR"/*.zip
rm -rf "$DIST_DIR"/lens-app-*

echo -e "${GREEN}✓ Build directories created${NC}"
echo ""

# Prepare package (single variant - auto-installs Python via winget)
echo "Preparing package..."
"$SCRIPT_DIR/common/prepare-package.sh" "$VERSION" "$BUILD_DIR" "$DIST_DIR"
"$SCRIPT_DIR/common/verify-package.sh" "$BUILD_DIR/lens-app" "requires-python"

echo ""
echo -e "${GREEN}✓ Windows package prepared and verified successfully!${NC}"
echo ""
echo "Package created in: $DIST_DIR"
echo "  - lens-package-requires-python-${VERSION}.zip"
echo ""
echo "Note: Installer will auto-install Python and ripgrep via winget if not already installed"
echo ""
echo "Next steps:"
echo "  1. Review the packages"
echo "  2. Commit and push to GitHub"
echo "  3. Trigger GitHub Actions workflow to create installers"
echo ""

