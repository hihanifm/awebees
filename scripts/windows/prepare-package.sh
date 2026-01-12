#!/bin/bash

# Prepare Windows package structure
# Usage: prepare-package.sh <version> <build_dir> <dist_dir>

set -e

VERSION=$1
BUILD_DIR=$2
DIST_DIR=$3

if [ -z "$VERSION" ] || [ -z "$BUILD_DIR" ] || [ -z "$DIST_DIR" ]; then
    echo "Usage: prepare-package.sh <version> <build_dir> <dist_dir>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_DIR="$BUILD_DIR/lens-app"

echo "Preparing Windows package..."

# Create package directory
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy VERSION file to package root
echo "  Copying VERSION file..."
cp "$PROJECT_ROOT/VERSION" "$PACKAGE_DIR/"

# Copy backend code
echo "  Copying backend code..."
mkdir -p "$PACKAGE_DIR/backend"
cp -r "$PROJECT_ROOT/backend/app" "$PACKAGE_DIR/backend/"
cp "$PROJECT_ROOT/backend/requirements.txt" "$PACKAGE_DIR/backend/"

# Copy sample files
echo "  Copying sample files..."
if [ -d "$PROJECT_ROOT/backend/samples" ]; then
    cp -r "$PROJECT_ROOT/backend/samples" "$PACKAGE_DIR/backend/"
    echo "  ✓ Sample files included"
else
    echo "  ⚠ Warning: samples directory not found"
fi

# Copy markdown documentation files (needed for help page)
echo "  Copying documentation files..."
# Copy main documentation files from project root
for doc_file in QUICK_START.md README.md FEATURES.md PLAYGROUND.md CHANGELOG.md WINDOWS-SETUP-GUIDE.md LOGGING_FEATURE.md E2E_TESTS.md; do
    if [ -f "$PROJECT_ROOT/$doc_file" ]; then
        cp "$PROJECT_ROOT/$doc_file" "$PACKAGE_DIR/"
    fi
done

# Copy docs subdirectory
if [ -d "$PROJECT_ROOT/docs" ]; then
    mkdir -p "$PACKAGE_DIR/docs"
    cp -r "$PROJECT_ROOT/docs"/* "$PACKAGE_DIR/docs/" 2>/dev/null || true
    echo "  ✓ Documentation subdirectory included"
fi

# Copy images referenced in documentation (if they exist)
echo "  Copying documentation images..."
for img_file in lens_1.png lens_2.png lens_3.png lensAI.png playground-screenshot.png playground_2nd.png; do
    if [ -f "$PROJECT_ROOT/$img_file" ]; then
        cp "$PROJECT_ROOT/$img_file" "$PACKAGE_DIR/"
    fi
done
echo "  ✓ Documentation files and images included"

# Copy frontend/out
echo "  Copying frontend build..."
# Create frontend directory first
mkdir -p "$PACKAGE_DIR/frontend"
# Copy the entire 'out' directory to 'frontend/out'
# Using trailing slash on source to copy contents, but we want the directory itself
cp -r "$PROJECT_ROOT/frontend/out" "$PACKAGE_DIR/frontend/"

# Copy Windows launcher scripts
echo "  Copying Windows launcher scripts..."
cp "$SCRIPT_DIR/lens-start.bat" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/lens-stop.bat" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/lens-status.bat" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/lens-logs.bat" "$PACKAGE_DIR/"

# Download ripgrep for Windows
echo "  Downloading ripgrep for Windows..."
RIPGREP_VERSION="14.1.0"
RIPGREP_URL="https://github.com/BurntSushi/ripgrep/releases/download/${RIPGREP_VERSION}/ripgrep-${RIPGREP_VERSION}-x86_64-pc-windows-msvc.zip"
RIPGREP_ZIP="$BUILD_DIR/ripgrep.zip"

mkdir -p "$PACKAGE_DIR/bin"

if [ ! -f "$RIPGREP_ZIP" ]; then
    curl -L -o "$RIPGREP_ZIP" "$RIPGREP_URL" || {
        echo "  ⚠ Warning: Failed to download ripgrep (optional tool)"
        RIPGREP_DOWNLOAD_FAILED=true
    }
fi

if [ "$RIPGREP_DOWNLOAD_FAILED" != "true" ] && [ -f "$RIPGREP_ZIP" ]; then
    unzip -q "$RIPGREP_ZIP" -d "$BUILD_DIR"
    cp "$BUILD_DIR/ripgrep-${RIPGREP_VERSION}-x86_64-pc-windows-msvc/rg.exe" "$PACKAGE_DIR/bin/"
    rm -rf "$BUILD_DIR/ripgrep-${RIPGREP_VERSION}-x86_64-pc-windows-msvc"
    echo "  ✓ ripgrep included for 10-100x faster pattern matching"
else
    echo "  ⚠ ripgrep not included (optional, can be installed later)"
fi

# Read build config
CONFIG_FILE="$SCRIPT_DIR/build-config.json"
if [ -f "$CONFIG_FILE" ]; then
    PYTHON_VERSION=$(grep -o '"python_version": "[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
else
    PYTHON_VERSION="3.11.9"
fi

# Create virtual environment structure (will be created on Windows during installation)
echo "  Creating virtual environment structure..."
mkdir -p "$PACKAGE_DIR/venv"
echo "  Dependencies will be installed on Windows during setup"

# Create ZIP archive
echo "  Creating ZIP archive..."
cd "$BUILD_DIR"
ZIP_NAME="lens-package-${VERSION}.zip"
zip -r "$DIST_DIR/$ZIP_NAME" "lens-app" > /dev/null

echo "  ✓ Package created: $ZIP_NAME"

