#!/bin/bash

# Prepare individual Windows package structure
# Usage: prepare-package.sh <variant> <version> <build_dir> <dist_dir>
# Variant: "with-python" or "requires-python"

set -e

VARIANT=$1
VERSION=$2
BUILD_DIR=$3
DIST_DIR=$4

if [ -z "$VARIANT" ] || [ -z "$VERSION" ] || [ -z "$BUILD_DIR" ] || [ -z "$DIST_DIR" ]; then
    echo "Usage: prepare-package.sh <variant> <version> <build_dir> <dist_dir>"
    exit 1
fi

if [ "$VARIANT" != "with-python" ] && [ "$VARIANT" != "requires-python" ]; then
    echo "Error: Variant must be 'with-python' or 'requires-python'"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_DIR="$BUILD_DIR/lens-app-$VARIANT"

echo "Preparing package: $VARIANT"

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

if [ "$VARIANT" = "with-python" ]; then
    echo "  Downloading embeddable Python..."
    PYTHON_EMBED_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-amd64.zip"
    PYTHON_ZIP="$BUILD_DIR/python-embed.zip"
    
    if [ ! -f "$PYTHON_ZIP" ]; then
        curl -L -o "$PYTHON_ZIP" "$PYTHON_EMBED_URL" || {
            echo "Error: Failed to download embeddable Python"
            exit 1
        }
    fi
    
    # Extract Python to package directory
    unzip -q "$PYTHON_ZIP" -d "$PACKAGE_DIR/python"
    
    # Create python._pth file for embedded Python
    PYTHON_ZIP_NAME="python${PYTHON_VERSION//./}.zip"
    cat > "$PACKAGE_DIR/python/python._pth" << EOF
$PYTHON_ZIP_NAME
.
import site
EOF
    
    echo "  Note: Virtual environment will be created on Windows during installation"
    echo "  Embedded Python will be used to install dependencies"
else
    echo "  Creating virtual environment structure..."
    # For requires-python, we'll create venv on Windows during installation
    # For now, just create the structure
    mkdir -p "$PACKAGE_DIR/venv"
    echo "  Dependencies will be installed on Windows during setup"
fi

# Install Python dependencies (only for with-python variant on Linux/Mac)
if [ "$VARIANT" = "with-python" ]; then
    echo "  Installing Python dependencies..."
    # Note: We can't actually install Windows Python packages on Linux/Mac
    # The installer will handle this, or we can create a requirements.txt marker
    echo "  Dependencies will be installed on Windows (embedded Python requires Windows environment)"
fi

# Create ZIP archive
echo "  Creating ZIP archive..."
cd "$BUILD_DIR"
ZIP_NAME="lens-package-${VARIANT}-${VERSION}.zip"
zip -r "$DIST_DIR/$ZIP_NAME" "lens-app-$VARIANT" > /dev/null

echo "  ✓ Package created: $ZIP_NAME"

