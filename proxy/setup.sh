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
CADDY_VERSION="2.7.6"
CADDY_URL="https://github.com/caddyserver/caddy/releases/download/v${CADDY_VERSION}/caddy_${CADDY_VERSION}_${CADDY_OS}_${CADDY_ARCH}.tar.gz"

echo ""
echo "Downloading Caddy v${CADDY_VERSION}..."
if command -v curl &> /dev/null; then
    curl -L -o caddy.tar.gz "$CADDY_URL"
elif command -v wget &> /dev/null; then
    wget -O caddy.tar.gz "$CADDY_URL"
else
    echo "Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi

echo "Extracting Caddy..."
tar -xzf caddy.tar.gz
rm caddy.tar.gz
chmod +x caddy

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
