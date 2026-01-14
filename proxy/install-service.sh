#!/bin/bash

# Install service for auto-start on reboot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OS="$(uname -s)"
USER_HOME="$HOME"
PROXY_DIR="$SCRIPT_DIR"

echo "=== Installing Service for Auto-Start ==="
echo ""

if [[ "$OS" == "Linux" ]]; then
    # Linux systemd installation
    echo "Installing systemd service..."
    
    # Create service file with actual paths
    SERVICE_FILE="/tmp/caddy-proxy-$$.service"
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Caddy Forward Proxy
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROXY_DIR
ExecStart=$PROXY_DIR/start.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="HOME=$USER_HOME"

[Install]
WantedBy=multi-user.target
EOF
    
    echo "Service file created. Installing to /etc/systemd/system/caddy-proxy.service..."
    echo "This requires sudo privileges."
    
    sudo cp "$SERVICE_FILE" /etc/systemd/system/caddy-proxy.service
    sudo systemctl daemon-reload
    sudo systemctl enable caddy-proxy.service
    sudo systemctl start caddy-proxy.service
    
    rm -f "$SERVICE_FILE"
    
    echo ""
    echo "Service installed and started!"
    echo ""
    echo "Useful commands:"
    echo "  sudo systemctl status caddy-proxy    # Check status"
    echo "  sudo systemctl stop caddy-proxy      # Stop service"
    echo "  sudo systemctl start caddy-proxy     # Start service"
    echo "  sudo systemctl restart caddy-proxy   # Restart service"
    
elif [[ "$OS" == "Darwin" ]]; then
    # macOS launchd installation
    echo "Installing launchd service..."
    
    LAUNCH_AGENTS_DIR="$USER_HOME/Library/LaunchAgents"
    mkdir -p "$LAUNCH_AGENTS_DIR"
    
    # Create plist file with actual paths
    PLIST_FILE="$LAUNCH_AGENTS_DIR/com.caddy.proxy.plist"
    
    cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.caddy.proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd "$PROXY_DIR" && ./start.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROXY_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROXY_DIR/logs/service.log</string>
    <key>StandardErrorPath</key>
    <string>$PROXY_DIR/logs/service.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>$USER_HOME</string>
    </dict>
</dict>
</plist>
EOF
    
    # Load the service
    launchctl load "$PLIST_FILE" 2>/dev/null || launchctl load -w "$PLIST_FILE"
    
    echo ""
    echo "Service installed and loaded!"
    echo ""
    echo "Useful commands:"
    echo "  launchctl list | grep caddy          # Check if loaded"
    echo "  launchctl unload ~/Library/LaunchAgents/com.caddy.proxy.plist  # Unload"
    echo "  launchctl load ~/Library/LaunchAgents/com.caddy.proxy.plist    # Load"
    
else
    echo "Error: Unsupported OS: $OS"
    exit 1
fi

echo ""
echo "Service will start automatically on system reboot."
