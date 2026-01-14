#!/bin/bash

# Start the forward proxy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load configuration
if [ ! -f config.env ]; then
    echo "Error: config.env not found. Please run ./setup.sh first."
    exit 1
fi

source config.env

# Check if already running
if [ -f proxy.pid ]; then
    PID=$(cat proxy.pid)
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Proxy is already running (PID: $PID)"
        exit 0
    else
        echo "Removing stale PID file..."
        rm -f proxy.pid
    fi
fi

# Validate configuration
if [ -z "$TARGET_HOST" ] || [ -z "$TARGET_PORT" ] || [ -z "$TARGET_PROTOCOL" ]; then
    echo "Error: TARGET_HOST, TARGET_PORT, and TARGET_PROTOCOL must be set in config.env"
    exit 1
fi

if [ -z "$LISTEN_HOST" ]; then
    LISTEN_HOST="0.0.0.0"
fi

if [ -z "$LISTEN_PORT" ]; then
    echo "Error: LISTEN_PORT must be set in config.env"
    exit 1
fi

if [ -z "$CADDY_BINARY" ]; then
    CADDY_BINARY="./caddy"
fi

# Check if Caddy exists
if [ ! -f "$CADDY_BINARY" ]; then
    echo "Error: Caddy binary not found at $CADDY_BINARY"
    echo "Please run ./setup.sh first to download Caddy."
    exit 1
fi

# Generate Caddyfile
echo "Generating Caddyfile..."
cat > Caddyfile <<EOF
{
    # Enable access logging
    log {
        output file logs/access.log
        format console
    }
}

:${LISTEN_PORT} {
    # Reverse proxy to target server
    reverse_proxy ${TARGET_PROTOCOL}://${TARGET_HOST}:${TARGET_PORT} {
        # Enable streaming for AI responses
        flush_interval -1
        
        # Preserve all headers
        header_up Host {host}
        header_up X-Forwarded-Host {host}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Real-IP {remote_host}
        
        # Transport settings for better streaming
        transport http {
            dial_timeout 30s
            response_header_timeout 30s
        }
    }
}
EOF

echo "Starting proxy on ${LISTEN_HOST}:${LISTEN_PORT}..."
echo "Forwarding to ${TARGET_PROTOCOL}://${TARGET_HOST}:${TARGET_PORT}"

# Start Caddy in background
nohup "$CADDY_BINARY" run --config Caddyfile > logs/caddy.log 2>&1 &
PID=$!

# Save PID
echo $PID > proxy.pid

# Wait a moment to check if it started successfully
sleep 1

if ps -p "$PID" > /dev/null 2>&1; then
    echo "Proxy started successfully (PID: $PID)"
    echo "Logs: logs/caddy.log"
    echo "Access logs: logs/access.log"
else
    echo "Error: Proxy failed to start. Check logs/caddy.log for details."
    rm -f proxy.pid
    exit 1
fi
