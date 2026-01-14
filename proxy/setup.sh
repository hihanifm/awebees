#!/bin/bash

# Forward Proxy Setup Script
# Installs Caddy and sets up the proxy configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Forward Proxy Setup ==="
echo ""

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected OS: $OS"
echo "Detected Architecture: $ARCH"

# Map architecture
case "$ARCH" in
    x86_64)
        CADDY_ARCH="amd64"
        ;;
    arm64|aarch64)
        CADDY_ARCH="arm64"
        ;;
    *)
        echo "Warning: Unknown architecture $ARCH, defaulting to amd64"
        CADDY_ARCH="amd64"
        ;;
esac

# Determine OS type and download URL
if [[ "$OS" == "Linux" ]]; then
    CADDY_OS="linux"
    echo "Platform: Linux ($CADDY_ARCH)"
elif [[ "$OS" == "Darwin" ]]; then
    CADDY_OS="darwin"
    echo "Platform: macOS ($CADDY_ARCH)"
else
    echo "Error: Unsupported OS: $OS"
    echo "This script supports Linux and macOS only."
    exit 1
fi

# Download Caddy
echo ""
echo "Downloading Caddy..."

# Use Caddy's official download API which returns the binary directly
CADDY_DOWNLOAD_URL="https://caddyserver.com/api/download?os=${CADDY_OS}&arch=${CADDY_ARCH}&id=standard"

echo "Download URL: $CADDY_DOWNLOAD_URL"

# Download the binary directly (Caddy API returns the binary, not an archive)
if command -v curl &> /dev/null; then
    if ! curl -L -f -o caddy "$CADDY_DOWNLOAD_URL" 2>/dev/null; then
        echo "Error: Failed to download from Caddy API, trying alternative method..."
        # Alternative: Try to get latest version from GitHub and construct URL
        CADDY_VERSION=$(curl -s https://api.github.com/repos/caddyserver/caddy/releases/latest | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/' | head -1)
        if [ -n "$CADDY_VERSION" ]; then
            CADDY_ALT_URL="https://github.com/caddyserver/caddy/releases/download/v${CADDY_VERSION}/caddy_${CADDY_VERSION}_${CADDY_OS}_${CADDY_ARCH}.tar.gz"
            echo "Trying GitHub release: $CADDY_ALT_URL"
            if curl -L -f -o caddy.tar.gz "$CADDY_ALT_URL" 2>/dev/null; then
                echo "Extracting from archive..."
                if tar -xzf caddy.tar.gz; then
                    rm -f caddy.tar.gz
                else
                    echo "Error: Failed to extract archive."
                    rm -f caddy.tar.gz
                    exit 1
                fi
            else
                echo "Error: Both download methods failed."
                echo ""
                echo "Please install Caddy manually:"
                if [[ "$OS" == "Darwin" ]]; then
                    echo "  macOS: brew install caddy"
                fi
                echo "  Or visit: https://caddyserver.com/download"
                exit 1
            fi
        else
            echo "Error: Could not determine Caddy version."
            exit 1
        fi
    fi
elif command -v wget &> /dev/null; then
    if ! wget -O caddy "$CADDY_DOWNLOAD_URL" 2>/dev/null; then
        echo "Error: Failed to download Caddy."
        exit 1
    fi
else
    echo "Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi

# Check if download was successful
if [ ! -f caddy ] || [ ! -s caddy ]; then
    echo "Error: Failed to download Caddy. The file is empty or doesn't exist."
    rm -f caddy
    exit 1
fi

# Check file size (should be more than a few bytes - Caddy binary is typically 30-50MB)
FILE_SIZE=$(stat -f%z caddy 2>/dev/null || stat -c%s caddy 2>/dev/null || echo "0")
if [ "$FILE_SIZE" -lt 1000000 ]; then
    echo "Error: Downloaded file is too small ($FILE_SIZE bytes). Download likely failed."
    echo "The response was:"
    head -20 caddy
    rm -f caddy
    exit 1
fi

chmod +x caddy

# Verify it works
if ./caddy version &>/dev/null; then
    CADDY_VER=$(./caddy version | head -1)
    echo "Download complete ($FILE_SIZE bytes)"
    echo "Caddy installed successfully: $CADDY_VER"
else
    echo "Download complete ($FILE_SIZE bytes)"
    echo "Warning: Caddy binary found but version check failed."
    echo "The binary might not be compatible, but continuing anyway..."
fi

echo "Caddy installed successfully!"
echo ""

# Create logs directory
mkdir -p logs

# Copy config.env.example to config.env if it doesn't exist
if [ ! -f config.env ]; then
    echo "Creating config.env from config.env.example..."
    cp config.env.example config.env
    echo "Configuration file created. Please review and edit config.env if needed."
else
    echo "config.env already exists, skipping..."
fi

# Make all scripts executable
chmod +x *.sh

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review and edit config.env if needed"
echo "2. Run ./start.sh to start the proxy"
echo "3. (Optional) Run ./install-service.sh to enable auto-start on reboot"
echo ""
