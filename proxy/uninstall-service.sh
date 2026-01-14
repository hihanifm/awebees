#!/bin/bash

# Uninstall service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OS="$(uname -s)"

echo "=== Uninstalling Service ==="
echo ""

if [[ "$OS" == "Linux" ]]; then
    # Linux systemd uninstallation
    echo "Stopping and disabling systemd service..."
    
    if systemctl is-active --quiet caddy-proxy.service 2>/dev/null; then
        sudo systemctl stop caddy-proxy.service
    fi
    
    if systemctl is-enabled --quiet caddy-proxy.service 2>/dev/null; then
        sudo systemctl disable caddy-proxy.service
    fi
    
    if [ -f /etc/systemd/system/caddy-proxy.service ]; then
        sudo rm /etc/systemd/system/caddy-proxy.service
        sudo systemctl daemon-reload
        echo "Service removed."
    else
        echo "Service file not found. It may have already been removed."
    fi
    
elif [[ "$OS" == "Darwin" ]]; then
    # macOS launchd uninstallation
    echo "Unloading launchd service..."
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.caddy.proxy.plist"
    
    if [ -f "$PLIST_FILE" ]; then
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        rm -f "$PLIST_FILE"
        echo "Service removed."
    else
        echo "Service file not found. It may have already been removed."
    fi
    
else
    echo "Error: Unsupported OS: $OS"
    exit 1
fi

echo ""
echo "Service uninstalled. The proxy will no longer start automatically on reboot."
echo "You can still start it manually with ./start.sh"
